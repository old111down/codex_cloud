#!/usr/bin/env python3
"""Read-only audit of this task's PCAP, official traffic_logs, and run metadata.

Inputs and the detailed evidence must remain under this audit's private/ root.
The summary is an explicit allow-list: no IPs, raw UUIDs, HTTP contents, or
ephemeral ports. Connection identity is linkage ground truth, never a feature.
This script opens no network sockets and starts no capture, service, or tc job.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from dataclasses import dataclass, field
import hashlib
import json
import math
import os
from pathlib import Path
import re
import socket
import sqlite3
import statistics
import struct
import sys
from typing import Any
from urllib.parse import urlsplit

import dpkt

ROOT = Path(__file__).resolve().parent.parent
PRIVATE = ROOT / "private"
PINNED_SHA = "d055fa68ef4de30b93a8a30838ae51fe3e4b561c"
NS = 1_000_000_000
SEND_METHODS = frozenset({"message/send", "SendMessage"})


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def private_path(path: Path) -> Path:
    path = path.resolve()
    if not path.is_relative_to(PRIVATE.resolve()):
        raise ValueError("raw inputs and detailed outputs must be under audit private/")
    return path


def resolve_input(run_dir: Path, raw: str | None, fallback: str) -> Path:
    path = Path(raw or fallback)
    return private_path(path if path.is_absolute() else run_dir / path)


def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError("metadata must contain a JSON object")
    return value


def write_json(path: Path, value: dict, private: bool = False) -> None:
    if private:
        private_path(path)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700 if private else 0o755)
    # Only our own named analyzer outputs may be replaced, never an input file.
    flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
    fd = os.open(path, flags, 0o600 if private else 0o644)
    if private:
        os.fchmod(fd, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        json.dump(value, handle, indent=2, ensure_ascii=False, allow_nan=False)
        handle.write("\n")


@dataclass
class Packet:
    index: int
    ts: int
    src: str
    sport: int
    dst: str
    dport: int
    seq: int
    ack: int
    flags: int
    data: bytes
    frame_len: int
    ip_version: int

    @property
    def source(self) -> tuple[str, int]:
        return self.src, self.sport

    @property
    def dest(self) -> tuple[str, int]:
        return self.dst, self.dport


@dataclass
class Flow:
    alias: str
    endpoints: tuple
    epoch: int
    packets: list[Packet] = field(default_factory=list)
    initial_syn: Packet | None = None


def read_pcap(path: Path) -> tuple[list[Packet], dict]:
    parsed: list[Packet] = []
    counts: Counter = Counter()
    with path.open("rb") as handle:
        header = handle.read(24)
        if len(header) != 24:
            raise ValueError("PCAP global header is absent or truncated")
        formats = {b"\x4d\x3c\xb2\xa1": ("<", 1), b"\xa1\xb2\x3c\x4d": (">", 1),
                   b"\xd4\xc3\xb2\xa1": ("<", 1000), b"\xa1\xb2\xc3\xd4": (">", 1000)}
        if header[:4] not in formats:
            raise ValueError("unsupported capture magic; classic PCAP required")
        endian, multiplier = formats[header[:4]]
        major, minor, _zone, _sig, snaplen, linktype = struct.unpack(endian + "HHIIII", header[4:])
        if (major, minor) != (2, 4) or linktype != 1:
            raise ValueError("PCAP must be version 2.4 DLT_EN10MB Ethernet")
        if multiplier != 1:
            raise ValueError("nanosecond classic PCAP required for this collector")
        last_ts = None
        while True:
            record = handle.read(16)
            if not record:
                break
            if len(record) != 16:
                raise ValueError("truncated PCAP record header")
            seconds, fraction, incl, orig = struct.unpack(endian + "IIII", record)
            if fraction >= NS or incl > snaplen or incl > orig or incl > 16 * 1024 * 1024:
                raise ValueError("invalid PCAP timestamp or record length")
            raw = handle.read(incl)
            if len(raw) != incl:
                raise ValueError("truncated PCAP packet record")
            counts["records"] += 1
            counts["frame_bytes"] += incl
            counts["truncated_records"] += int(incl != orig)
            timestamp = seconds * NS + fraction
            if last_ts is not None and timestamp < last_ts:
                counts["timestamp_regressions"] += 1
            last_ts = timestamp
            try:
                ethernet = dpkt.ethernet.Ethernet(raw)
                counts["ethernet"] += 1
                ip = ethernet.data
                if isinstance(ip, dpkt.ip.IP):
                    counts["ipv4"] += 1
                    if ip.offset or ip.mf:
                        counts["fragmented_ip"] += 1
                        continue
                    af, version = socket.AF_INET, 4
                elif isinstance(ip, dpkt.ip6.IP6):
                    counts["ipv6"] += 1
                    af, version = socket.AF_INET6, 6
                else:
                    counts["non_ip"] += 1
                    continue
                tcp = ip.data
                if not isinstance(tcp, dpkt.tcp.TCP):
                    counts["non_tcp_ip"] += 1
                    continue
                counts["tcp"] += 1
                parsed.append(Packet(counts["records"], timestamp,
                    socket.inet_ntop(af, ip.src), tcp.sport,
                    socket.inet_ntop(af, ip.dst), tcp.dport,
                    tcp.seq, tcp.ack, tcp.flags, bytes(tcp.data), incl, version))
            except (dpkt.Error, ValueError, IndexError, struct.error):
                counts["decode_errors"] += 1
    return parsed, {"format": "classic_pcap_nanosecond", "datalink": linktype,
                    "snaplen": snaplen, "counts": dict(counts),
                    "nonempty": bool(counts["records"])}


def make_flows(packets: list[Packet]) -> list[Flow]:
    current: dict[tuple, Flow] = {}
    epochs: Counter = Counter()
    flows = []
    for packet in packets:
        key = tuple(sorted((packet.source, packet.dest)))
        old = current.get(key)
        syn = bool(packet.flags & dpkt.tcp.TH_SYN and not packet.flags & dpkt.tcp.TH_ACK)
        new_epoch = old is None or (syn and (old.initial_syn is None or
            old.initial_syn.source != packet.source or old.initial_syn.seq != packet.seq or
            any(p.flags & (dpkt.tcp.TH_FIN | dpkt.tcp.TH_RST) for p in old.packets)))
        if new_epoch:
            epochs[key] += 1
            old = Flow(f"connection_{len(flows) + 1:03d}", key, epochs[key])
            current[key] = old
            flows.append(old)
        if syn and old.initial_syn is None:
            old.initial_syn = packet
        old.packets.append(packet)
    return flows


def relative_seq(sequence: int, base: int) -> int:
    return ((sequence - base + (1 << 31)) % (1 << 32)) - (1 << 31)


def reassemble(packets: list[Packet]) -> tuple[bytes, list[int], dict]:
    payloads = [p for p in packets if p.data]
    if not payloads:
        return b"", [], {"unique_payload_bytes": 0, "retransmitted_payload_bytes": 0,
                           "conflicting_overlap_bytes": 0, "gap_bytes": 0}
    base = (payloads[0].seq + bool(payloads[0].flags & dpkt.tcp.TH_SYN)) % (1 << 32)
    cells: dict[int, tuple[int, int]] = {}
    retrans = conflicts = 0
    for packet in payloads:
        offset = relative_seq((packet.seq + bool(packet.flags & dpkt.tcp.TH_SYN)) % (1 << 32), base)
        if abs(offset) > 64 * 1024 * 1024:
            raise ValueError("TCP sequence range exceeds this bounded task analyzer")
        for i, value in enumerate(packet.data, offset):
            if i in cells:
                retrans += 1
                conflicts += int(cells[i][0] != value)
                if packet.ts < cells[i][1]:
                    cells[i] = (cells[i][0], packet.ts)
            else:
                cells[i] = (value, packet.ts)
    low, high = min(cells), max(cells)
    gaps = high - low + 1 - len(cells)
    # Never bridge holes with fabricated bytes. HTTP evidence requires no gaps.
    if gaps:
        return b"", [], {"unique_payload_bytes": len(cells),
            "retransmitted_payload_bytes": retrans, "conflicting_overlap_bytes": conflicts,
            "gap_bytes": gaps}
    return bytes(cells[i][0] for i in range(low, high + 1)), [cells[i][1] for i in range(low, high + 1)], {
        "unique_payload_bytes": len(cells), "retransmitted_payload_bytes": retrans,
        "conflicting_overlap_bytes": conflicts, "gap_bytes": 0}


def decode_chunked(data: bytes, offset: int) -> tuple[bytes, int]:
    chunks = []
    cursor = offset
    while True:
        end = data.find(b"\r\n", cursor)
        if end < 0:
            raise ValueError("incomplete HTTP chunk size")
        size = int(data[cursor:end].split(b";", 1)[0], 16)
        cursor = end + 2
        if size == 0:
            if data[cursor:cursor + 2] == b"\r\n":
                return b"".join(chunks), cursor + 2
            trailers = data.find(b"\r\n\r\n", cursor)
            if trailers < 0:
                raise ValueError("incomplete HTTP chunk trailers")
            return b"".join(chunks), trailers + 4
        if size < 0 or cursor + size + 2 > len(data) or data[cursor + size:cursor + size + 2] != b"\r\n":
            raise ValueError("incomplete HTTP chunk data")
        chunks.append(data[cursor:cursor + size])
        cursor += size + 2


def parse_http(data: bytes, timestamps: list[int], response: bool) -> tuple[list[dict], list[str]]:
    messages = []
    errors = []
    cursor = 0
    while cursor < len(data):
        start = cursor
        boundary = data.find(b"\r\n\r\n", start)
        if boundary < 0:
            errors.append("incomplete_http_header")
            break
        lines = data[start:boundary].split(b"\r\n")
        first = lines[0].decode("latin1")
        if (response and not first.startswith("HTTP/1.1 ")) or (not response and not re.match(r"^[A-Z]+ \S+ HTTP/1\.1$", first)):
            errors.append("not_http_1_1")
            break
        headers: dict[str, str] = {}
        try:
            for line in lines[1:]:
                name, value = line.split(b":", 1)
                key = name.decode("latin1").lower()
                if key in headers and key in ("content-length", "transfer-encoding"):
                    raise ValueError("duplicate framing header")
                headers[key] = value.decode("latin1").strip()
            body_start = boundary + 4
            if headers.get("transfer-encoding", "").lower() == "chunked":
                body, cursor = decode_chunked(data, body_start)
            elif "content-length" in headers:
                length = int(headers["content-length"])
                if length < 0 or body_start + length > len(data):
                    raise ValueError("incomplete HTTP content-length body")
                cursor = body_start + length
                body = data[body_start:cursor]
            elif response:
                code = int(first.split()[1])
                if code not in (204, 304) and not 100 <= code < 200:
                    raise ValueError("response lacks explicit message framing")
                cursor, body = body_start, b""
            else:
                cursor, body = body_start, b""
            message = {"start_line": first, "headers": headers,
                "body_text": body.decode("utf-8", errors="replace"),
                "body_sha256": sha256_bytes(body), "body_bytes": len(body),
                "wire_bytes": cursor - start,
                "first_byte_wall_ns": min(timestamps[start:cursor]),
                "last_byte_wall_ns": max(timestamps[start:cursor])}
            try:
                message["json"] = json.loads(body)
            except (ValueError, UnicodeError):
                message["json"] = None
            messages.append(message)
        except (ValueError, IndexError):
            errors.append("invalid_or_incomplete_http_framing")
            break
    return messages, errors


def part_texts(value: Any) -> list[str]:
    """Extract text only from explicit A2A text parts, not incidental strings."""
    found = []
    if isinstance(value, dict):
        if isinstance(value.get("text"), str) and value.get("kind", "text") == "text":
            found.append(value["text"])
        else:
            for nested in value.values():
                found.extend(part_texts(nested))
    elif isinstance(value, list):
        for nested in value:
            found.extend(part_texts(nested))
    return found


def response_text(result: Any) -> str:
    """Follow the official SDK's task-artifact/message text projection.

    A Task's history contains the user's input and is not output text. SDK
    1.1.0 wraps its result in {task: ...}; older JSON-RPC uses a direct Task.
    The selected deterministic echo has one reply artifact with one text part.
    """
    if not isinstance(result, dict):
        return ""
    task = result.get("task", result)
    if isinstance(task, dict) and isinstance(task.get("artifacts"), list):
        return "\n".join("\n".join(part_texts(a.get("parts", [])))
                         for a in task["artifacts"] if isinstance(a, dict))
    message = result.get("message", result)
    return "\n".join(part_texts(message.get("parts", []))) if isinstance(message, dict) else ""


def handshake(flow: Flow, server: tuple) -> dict:
    syn = flow.initial_syn
    if syn is None or syn.dest != server:
        return {"status": "missing_client_syn", "syn_to_synack_ms": None}
    matching = [p for p in flow.packets if p.source == server and p.dest == syn.source
                and p.flags & dpkt.tcp.TH_SYN and p.flags & dpkt.tcp.TH_ACK
                and p.ack == (syn.seq + 1) % (1 << 32) and p.ts >= syn.ts]
    if not matching:
        return {"status": "missing_matching_synack", "syn_to_synack_ms": None}
    synack = min(matching, key=lambda p: p.ts)
    syns = [p for p in flow.packets if p.source == syn.source and p.dest == server
            and p.flags & dpkt.tcp.TH_SYN and not p.flags & dpkt.tcp.TH_ACK
            and p.seq == syn.seq]
    thirds = [p for p in flow.packets if p.source == syn.source and p.dest == server
              and p.flags & dpkt.tcp.TH_ACK and not p.flags & dpkt.tcp.TH_SYN
              and p.ack == (synack.seq + 1) % (1 << 32)
              and p.seq == (syn.seq + 1) % (1 << 32) and p.ts >= synack.ts]
    unambiguous = len(syns) == len(matching) == 1
    return {"status": "matched_three_way" if thirds and unambiguous else
                "retransmission_ambiguous_rtt" if not unambiguous else "missing_third_ack",
        "syn_packet_index": syn.index,
        "synack_packet_index": synack.index, "syn_seq": syn.seq, "synack_seq": synack.seq,
        "synack_ack": synack.ack, "syn_wall_ns": syn.ts, "synack_wall_ns": synack.ts,
        "syn_to_synack_ms": (synack.ts - syn.ts) / 1_000_000 if unambiguous and thirds else None,
        "client_syn_count": len(syns), "matching_synack_count": len(matching),
        "third_ack_seen": bool(thirds),
        "syn_to_third_ack_ms_not_rtt": (min(p.ts for p in thirds) - syn.ts) / 1_000_000 if thirds else None,
        "measurement": "same_capture_client_SYN_to_reverse_matching_SYN_ACK_receive_timestamp_delta"}


def analyze_flow(flow: Flow, service_port: int) -> dict:
    servers = [end for end in flow.endpoints if end[1] == service_port]
    if len(servers) != 1:
        return {"alias": flow.alias, "errors": ["ambiguous_server_endpoint"]}
    server = servers[0]
    client = next(end for end in flow.endpoints if end != server)
    up = [p for p in flow.packets if p.source == client]
    down = [p for p in flow.packets if p.source == server]
    request_data, request_times, up_stat = reassemble(up)
    response_data, response_times, down_stat = reassemble(down)
    requests, request_errors = parse_http(request_data, request_times, False)
    responses, response_errors = parse_http(response_data, response_times, True)
    return {"alias": flow.alias, "tuple_epoch": flow.epoch,
        "client": {"ip": client[0], "port": client[1]},
        "server": {"ip": server[0], "port": server[1]},
        "first_wall_ns": min(p.ts for p in flow.packets),
        "last_wall_ns": max(p.ts for p in flow.packets),
        "packets": len(flow.packets), "frame_bytes": sum(p.frame_len for p in flow.packets),
        "client_to_server_packets": len(up), "server_to_client_packets": len(down),
        "both_directions": bool(up and down),
        "client_to_server_reassembly": up_stat, "server_to_client_reassembly": down_stat,
        "requests": requests, "responses": responses,
        "http_errors": request_errors + response_errors, "handshake": handshake(flow, server)}


def anchor(run: dict, kind: str) -> dict | None:
    for key in (kind, kind + "_anchor"):
        value = run.get(key)
        if isinstance(value, dict) and "wall_ns" in value:
            return value
    value = run.get("anchors", {}).get(kind) if isinstance(run.get("anchors"), dict) else None
    return value if isinstance(value, dict) else None


def clock_evidence(run: dict) -> dict:
    start, end = anchor(run, "start"), anchor(run, "end")
    if not start or not end:
        return {"status": "missing_run_clock_anchors"}
    result = {"status": "valid", "anchors": {"start": start, "end": end}}
    intervals = []
    for value in (start, end):
        try:
            before, wall, after = (int(value[k]) for k in ("mono_before_ns", "wall_ns", "mono_after_ns"))
            if after < before:
                raise ValueError("reversed monotonic sandwich")
            intervals.append((wall - after, wall - before))
        except (KeyError, ValueError, TypeError):
            result["status"] = "invalid_run_clock_anchors"
            return result
    result["wall_minus_monotonic_interval_ns"] = intervals
    result["max_anchor_read_bracket_ns"] = max(v["mono_after_ns"] - v["mono_before_ns"] for v in (start, end))
    result["offset_midpoint_change_ns"] = (sum(intervals[1]) - sum(intervals[0])) / 2
    if end["wall_ns"] < start["wall_ns"]:
        result["status"] = "reversed_run_wall_window"
    return result


def collector_clock_evidence(capture: dict) -> dict:
    values = capture.get("clock_anchors", [])
    centers, brackets = [], []
    last_mono = last_wall = None
    try:
        for value in values:
            before, wall, after = (int(value[k]) for k in ("mono_before_ns", "wall_ns", "mono_after_ns"))
            if after < before or (last_mono is not None and before < last_mono) or (last_wall is not None and wall < last_wall):
                raise ValueError("invalid collector clock order")
            # Keep doubled midpoints as integers until after subtraction.
            # Absolute realtime-minus-monotonic values exceed float ns precision.
            centers.append(2 * wall - before - after)
            brackets.append(after - before)
            last_mono, last_wall = after, wall
    except (KeyError, ValueError, TypeError):
        return {"status": "invalid_collector_clock_anchors", "anchor_count": len(values)}
    return {"status": "valid" if len(values) >= 2 else "missing_collector_clock_anchors",
        "anchor_count": len(values), "max_anchor_read_bracket_ns": max(brackets) if brackets else None,
        "offset_midpoint_range_ns": (max(centers) - min(centers)) / 2 if centers else None,
        "offset_midpoint_start_end_change_ns": (centers[-1] - centers[0]) / 2 if centers else None}


def read_app_db(path: Path) -> tuple[list[dict], dict]:
    with sqlite3.connect(path.as_uri() + "?mode=ro", uri=True) as conn:
        conn.row_factory = sqlite3.Row
        check = conn.execute("PRAGMA quick_check").fetchone()[0]
        columns = [r[1] for r in conn.execute("PRAGMA table_info(traffic_logs)")]
        required = {"id", "session_id", "scenario_id", "t_request_start", "t_last_token", "latency_sec", "success", "metadata"}
        if not required <= set(columns):
            raise ValueError("official traffic_logs required columns are absent")
        records = [dict(r) for r in conn.execute("SELECT * FROM traffic_logs ORDER BY id")]
    for row in records:
        try:
            row["parsed_metadata"] = json.loads(row.get("metadata") or "{}")
        except (ValueError, TypeError):
            row["parsed_metadata"] = {}
    return records, {"quick_check": check, "rows": len(records), "schema_columns": columns}


def finite(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def ms_stats(values: list[float]) -> dict:
    return {"sample_count": len(values), "samples_ms": values,
            "median_ms": statistics.median(values) if values else None,
            "min_ms": min(values) if values else None, "max_ms": max(values) if values else None}


def audit(run_dir: Path) -> tuple[dict, dict]:
    run = load_json(run_dir / "run.json")
    run_alias = run.get("run_id", run_dir.name)
    if not isinstance(run_alias, str) or not re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]{0,47}", run_alias):
        raise ValueError("run_id must be a short synthetic public alias")
    pcap_path = resolve_input(run_dir, run.get("pcap_path"), "capture.pcap")
    meta_path = resolve_input(run_dir, run.get("capture_meta_path"), "capture.json")
    db_path = resolve_input(run_dir, run.get("appdb_path", run.get("app_db_path")), "app.db")
    capture = load_json(meta_path)
    packets, pcap = read_pcap(pcap_path)
    rows, database = read_app_db(db_path)
    source_sha = run.get("source_sha")
    target_port = int(run.get("target_port", 9001))
    negative_port = int(run.get("negative_port", 9009))
    if target_port == negative_port:
        raise ValueError("target and negative ports must differ")
    target_packets = [p for p in packets if target_port in (p.sport, p.dport)]
    negative_packets = [p for p in packets if negative_port in (p.sport, p.dport)]
    target_flows = [analyze_flow(f, target_port) for f in make_flows(target_packets)]
    negative_flows = [analyze_flow(f, negative_port) for f in make_flows(negative_packets)]
    clock = clock_evidence(run)
    collector_clock = collector_clock_evidence(capture)
    failures = []
    checks = {}
    checks["source_revision_pinned"] = source_sha == PINNED_SHA
    checks["run_alias_matches_directory"] = run_alias == run_dir.name
    checks["nonempty_ethernet_ip_tcp"] = bool(target_packets) and pcap["counts"].get("tcp", 0) == pcap["counts"].get("records", 0)
    checks["no_truncation_decode_or_time_regression"] = not any(pcap["counts"].get(k, 0) for k in ("truncated_records", "decode_errors", "fragmented_ip", "timestamp_regressions"))
    checks["interface_consistent"] = run.get("interface") == capture.get("interface") == "lo"
    checks["capture_ports_match_run_scope"] = set(capture.get("ports", [])) == {target_port, negative_port}
    checks["capture_metadata_complete"] = capture.get("status") == "completed" and capture.get("datalink") == 1 and capture.get("packet_type_retained") == "PACKET_HOST(0)"
    scope = capture.get("namespace_scope", {})
    checks["capture_namespace_manifest_consistent"] = bool(scope.get("netns") and scope.get("netns") == run.get("namespace") and scope.get("netns") != scope.get("recorded_parent_netns"))
    checks["capture_socket_drained_after_stop"] = capture.get("socket_drained_after_stop") is True
    stats = capture.get("packet_socket_statistics", {})
    checks["capture_socket_zero_reported_drops"] = stats.get("tp_drops") == 0
    checks["capture_hash_and_count_match"] = (capture.get("pcap_sha256") == sha256_file(pcap_path) and capture.get("counts", {}).get("retained_packets") == pcap["counts"].get("records", 0))
    checks["official_db_integrity"] = database["quick_check"] == "ok"
    checks["run_clock_anchors_valid"] = clock["status"] == "valid"
    checks["collector_clock_anchors_valid"] = collector_clock["status"] == "valid"
    checks["process_exit_zero"] = run.get("process_exit") == 0
    start_anchor, end_anchor = anchor(run, "start"), anchor(run, "end")
    tolerance_ns = int(run.get("alignment_tolerance_ns", 50_000_000))
    if tolerance_ns < 0 or tolerance_ns > NS:
        raise ValueError("alignment_tolerance_ns must be between zero and one second")
    matching_rows = []
    for row in rows:
        meta = row["parsed_metadata"]
        start, end = row.get("t_request_start"), row.get("t_last_token")
        valid = finite(start) and finite(end) and start > 0 and end >= start
        valid = valid and meta.get("protocol") == "a2a" and meta.get("record_type") == "a2a_task" and not bool(row.get("is_streaming"))
        if start_anchor and end_anchor and valid:
            valid = (start_anchor["wall_ns"] - tolerance_ns <= round(start * NS) <= round(end * NS) <= end_anchor["wall_ns"] + tolerance_ns)
        else:
            valid = False
        if run.get("app_session_id"):
            valid = valid and row.get("session_id") == run["app_session_id"]
        if run.get("scenario_id"):
            valid = valid and row.get("scenario_id") == run["scenario_id"]
        if valid:
            matching_rows.append(row)
    checks["exactly_one_official_app_task"] = len(matching_rows) == 1
    app_row = matching_rows[0] if len(matching_rows) == 1 else None
    checks["scenario_manifest_consistent"] = bool(app_row and app_row.get("scenario_id") == run.get("scenario_id", run.get("scenario")))
    task_text = run.get("task_text")
    task_hash = run.get("task_sha256")
    expected = run.get("expected_response_text", "echo: " + task_text if isinstance(task_text, str) else None)
    checks["private_task_hash_valid"] = isinstance(task_hash, str) and (task_text is None or (isinstance(task_text, str) and sha256_bytes(task_text.encode()) == task_hash))
    candidates = []
    protocol_candidates = []
    for flow in target_flows:
        flow_candidates = []
        requests, responses = flow.get("requests", []), flow.get("responses", [])
        for req_index, request in enumerate(requests):
            request_json = request.get("json")
            if not isinstance(request_json, dict) or not request["start_line"].startswith("POST ") or request_json.get("method") not in SEND_METHODS or request_json.get("jsonrpc") != "2.0":
                continue
            prompt_parts = part_texts(request_json.get("params", {}).get("message", {}))
            prompt = "".join(prompt_parts)
            prompt_hash = sha256_bytes(prompt.encode())
            # HTTP/1.1 request/response order is the primary pairing; JSON-RPC
            # IDs must independently agree. Informational responses excluded.
            finals = [r for r in responses if int(r["start_line"].split()[1]) >= 200]
            response = finals[req_index] if req_index < len(finals) else None
            response_json = response.get("json") if response else None
            reply_text = response_text(response_json.get("result", {})) if isinstance(response_json, dict) else ""
            result = response_json.get("result", {}) if isinstance(response_json, dict) else {}
            task_result = result.get("task", result) if isinstance(result, dict) else {}
            task_state = task_result.get("status", {}).get("state") if isinstance(task_result, dict) else None
            try:
                agent_url = urlsplit(app_row["parsed_metadata"].get("agent_url", "")) if app_row else None
                endpoint_ok = bool(agent_url and agent_url.scheme == "http" and
                    agent_url.hostname == flow["server"]["ip"] and (agent_url.port or 80) == flow["server"]["port"])
            except ValueError:
                endpoint_ok = False
            pair_checks = {"both_directions": flow.get("both_directions", False),
                "official_agent_endpoint_matches": endpoint_ok,
                "gap_free_conflict_free_tcp": all(flow.get(k, {}).get("gap_bytes", 1) == 0 and flow.get(k, {}).get("conflicting_overlap_bytes", 1) == 0 for k in ("client_to_server_reassembly", "server_to_client_reassembly")),
                "http_framing_complete": not flow.get("http_errors"),
                "request_task_hash_matches": bool(task_hash and prompt_hash == task_hash),
                "response_http_success": bool(response and 200 <= int(response["start_line"].split()[1]) < 300),
                "jsonrpc_id_matches": bool(isinstance(response_json, dict) and "id" in request_json and request_json["id"] is not None and response_json.get("id") == request_json["id"]),
                "jsonrpc_result_no_error": bool(isinstance(response_json, dict) and "result" in response_json and "error" not in response_json),
                "a2a_task_completed": task_state in ("completed", "TASK_STATE_COMPLETED"),
                "deterministic_response_matches": isinstance(expected, str) and reply_text == expected,
                "official_task_wall_window": bool(app_row and response and
                    round(app_row["t_request_start"] * NS) - tolerance_ns <= request["first_byte_wall_ns"] <= request["last_byte_wall_ns"] <= round(app_row["t_last_token"] * NS) + tolerance_ns and
                    request["first_byte_wall_ns"] <= response["first_byte_wall_ns"] <= response["last_byte_wall_ns"] <= round(app_row["t_last_token"] * NS) + tolerance_ns)}
            item = {"connection_alias": flow["alias"], "request_index": req_index,
                "observed_rpc_method": request_json["method"],
                "request_jsonrpc_id": request_json.get("id"),
                "request_text": prompt, "request_text_sha256": prompt_hash,
                "response_text": reply_text, "response_text_sha256": sha256_bytes(reply_text.encode()),
                "checks": pair_checks, "request_first_byte_wall_ns": request["first_byte_wall_ns"],
                "request_last_byte_wall_ns": request["last_byte_wall_ns"],
                "response_first_byte_wall_ns": response["first_byte_wall_ns"] if response else None,
                "response_last_byte_wall_ns": response["last_byte_wall_ns"] if response else None}
            item["within_unexpanded_official_task_window"] = bool(app_row and response and
                round(app_row["t_request_start"] * NS) <= request["first_byte_wall_ns"] <= request["last_byte_wall_ns"] <=
                response["first_byte_wall_ns"] <= response["last_byte_wall_ns"] <= round(app_row["t_last_token"] * NS))
            protocol_candidates.append(item)
            if all(pair_checks.values()):
                flow_candidates.append(item)
                candidates.append(item)
        flow["eligible_task_matches"] = len(flow_candidates)
    candidate_connections = sorted({c["connection_alias"] for c in candidates})
    match_status = "unique_connection" if len(candidate_connections) == 1 and len(candidates) == 1 else "ambiguous" if candidates or len(matching_rows) > 1 else "unmatched"
    checks["unique_target_connection_and_task"] = match_status == "unique_connection"
    checks["official_task_success"] = bool(app_row and app_row.get("success") == 1 and app_row.get("http_status") == 200)
    negative = run.get("negative_control", {})
    negative_matches = []
    for flow in negative_flows:
        client, server = negative.get("client"), negative.get("server")
        if client is None and negative.get("client_ip"):
            client = {"ip": negative["client_ip"], "port": negative.get("client_port")}
        if server is None and negative.get("server_ip"):
            server = {"ip": negative["server_ip"], "port": negative.get("server_port")}
        tuple_ok = flow.get("client") == client and flow.get("server") == server
        ns_start, ns_end = negative.get("start_wall_ns"), negative.get("end_wall_ns")
        window_ok = finite(ns_start) and finite(ns_end) and ns_start - tolerance_ns <= flow.get("first_wall_ns", 0) <= flow.get("last_wall_ns", 0) <= ns_end + tolerance_ns
        if tuple_ok and window_ok and flow.get("both_directions"):
            negative_matches.append(flow["alias"])
    negative_protocol_messages = sum(1 for f in negative_flows for r in f.get("requests", []) if isinstance(r.get("json"), dict) and r["json"].get("method") in SEND_METHODS)
    checks["negative_control_seen_exactly_once"] = len(negative_matches) == 1
    checks["negative_control_excluded_from_target"] = bool(negative_matches) and not any(negative_port in (p.sport, p.dport) for p in target_packets)
    checks["negative_control_protocol_rejected"] = bool(negative_matches) and negative_protocol_messages == 0
    checks["negative_control_manifest_success"] = negative.get("success") is True
    matched_flow = next((f for f in target_flows if candidate_connections == [f["alias"]]), None)
    selected = candidates[0] if match_status == "unique_connection" else None
    checks["matched_connection_three_way_handshake"] = bool(selected and matched_flow and matched_flow["handshake"].get("status") == "matched_three_way")
    for key, value in checks.items():
        if not value:
            failures.append(key)
    rtt = [matched_flow["handshake"]["syn_to_synack_ms"]] if selected and matched_flow and matched_flow["handshake"].get("syn_to_synack_ms") is not None else []
    latency_ms = app_row["latency_sec"] * 1000 if app_row and finite(app_row.get("latency_sec")) else None
    wire_elapsed = (selected["response_last_byte_wall_ns"] - selected["request_first_byte_wall_ns"]) / 1_000_000 if selected else None
    public = {"schema_version": "task-capture-analysis-v1", "run_alias": run_alias,
        "group": run.get("group") if run.get("group") in ("A", "B", "smoke", "scenario") else None, "source_sha": source_sha,
        "status": "PASS" if not failures else "FAIL", "match_status": match_status,
        "failure_reasons": failures, "checks": checks,
        "matching_granularity": "one_official_wall_clock_task_to_unique_HTTP_1_1_JSONRPC_A2A_send_connection",
        "observed_rpc_methods": sorted({c["observed_rpc_method"] for c in protocol_candidates}),
        "canonical_operation": "nonstreaming_A2A_send_message",
        "per_packet_sdk_event_ground_truth": False,
        "target_filter_counts": {"packets": len(target_packets), "frame_bytes": sum(p.frame_len for p in target_packets), "connections": len(target_flows),
            "client_to_server_packets": sum(f.get("client_to_server_packets", 0) for f in target_flows), "server_to_client_packets": sum(f.get("server_to_client_packets", 0) for f in target_flows)},
        "matched_connection_counts": {k: matched_flow[k] for k in ("packets", "frame_bytes", "client_to_server_packets", "server_to_client_packets")} if selected and matched_flow else None,
        "protocol_message_send_candidates": len(protocol_candidates), "eligible_task_candidates": len(candidates), "eligible_connections": len(candidate_connections),
        "protocol_candidate_rejection_counts": dict(Counter(key for c in protocol_candidates for key, passed in c["checks"].items() if not passed)),
        "app_record_match_status": "unique" if len(matching_rows) == 1 else "ambiguous" if matching_rows else "unmatched",
        "negative_control": {"packets": len(negative_packets), "connections": len(negative_flows), "matching_manifest_connections": len(negative_matches),
            "protocol_message_send_messages": negative_protocol_messages, "included_in_target_packet_counts": False,
            "rejection_reasons": ["different_target_endpoint", "no_A2A_send_method"] if negative_matches and negative_protocol_messages == 0 else []},
        "official_app_task_count": len(matching_rows), "official_app_latency_ms": latency_ms,
        "pcap_http_request_to_response_complete_ms": wire_elapsed,
        "syn_to_synack_rtt": ms_stats(rtt),
        "clock": {"status": clock["status"], "max_anchor_read_bracket_ns": clock.get("max_anchor_read_bracket_ns"), "offset_midpoint_change_ns": clock.get("offset_midpoint_change_ns"),
            "collector": collector_clock, "predeclared_matching_tolerance_ns": tolerance_ns,
            "matching_tolerance_is_measured_clock_error": False,
            "app_timestamp_float_ulp_ns": math.ulp(app_row["t_request_start"]) * NS if app_row else None,
            "matched_within_unexpanded_official_task_window": selected["within_unexpanded_official_task_window"] if selected else None},
        "hashes": {"pcap_sha256": sha256_file(pcap_path), "appdb_sha256": sha256_file(db_path), "run_json_sha256": sha256_file(run_dir / "run.json"), "task_sha256": task_hash},
        "capture_validation": {"nonempty": pcap["nonempty"], "datalink": pcap["datalink"], "format": pcap["format"], "reported_socket_drops": stats.get("tp_drops")},
        "limits": ["Connection linkage uses interface, task run, endpoint, task-time window, HTTP/1.1 and JSON-RPC evidence; these are ground truth, not classifier features.",
            "SYN-to-SYNACK is a same-capture receive-timestamp delta, distinct from SYN-to-third-ACK and official application latency.",
            "Nanosecond timestamp representation does not establish nanosecond measurement accuracy.",
            "One connection-level task match does not validate per-packet SDK events or arbitrary reused-connection tasks.",
            "Packet/frame byte counts include TCP ACKs and Ethernet/IP/TCP framing; official HTTP serialization counters have different scope.",
            "No network emulation or RTT intervention contrast is inferred by this analyzer."]}
    detailed = {"schema_version": public["schema_version"], "run": run, "capture_metadata": capture,
        "pcap_validation": pcap, "database_validation": database, "official_records": rows,
        "matching_official_record_ids": [r["id"] for r in matching_rows], "target_flows": target_flows,
        "negative_flows": negative_flows, "protocol_candidates": protocol_candidates,
        "eligible_candidates": candidates, "negative_matching_aliases": negative_matches,
        "clock_evidence": clock, "collector_clock_evidence": collector_clock, "summary": public}
    return detailed, public


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--private-output", required=True)
    parser.add_argument("--summary-output", required=True)
    args = parser.parse_args()
    outputs_validated = False
    try:
        run_dir = private_path(Path(args.run_dir))
        detailed_path = private_path(Path(args.private_output))
        summary_path = Path(args.summary_output).resolve()
        run = load_json(run_dir / "run.json")
        protected = {(run_dir / "run.json").resolve(),
            resolve_input(run_dir, run.get("pcap_path"), "capture.pcap"),
            resolve_input(run_dir, run.get("capture_meta_path"), "capture.json"),
            resolve_input(run_dir, run.get("appdb_path", run.get("app_db_path")), "app.db")}
        if detailed_path == summary_path or detailed_path in protected or summary_path in protected:
            raise ValueError("output paths must be distinct and must not replace raw inputs")
        outputs_validated = True
        detailed, summary = audit(run_dir)
        write_json(detailed_path, detailed, private=True)
        write_json(summary_path, summary)
        print(json.dumps({"run_alias": summary["run_alias"], "status": summary["status"],
                          "match_status": summary["match_status"], "failure_reasons": summary["failure_reasons"]}))
        return 0 if summary["status"] == "PASS" else 2
    except Exception as exc:
        # Failure to read/validate an input is distinct from a completed capture
        # whose task does not match. Keep such runs visible in the denominator.
        blocked = {"schema_version": "task-capture-analysis-v1", "status": "BLOCKED",
            "match_status": "not_evaluable", "error_class": type(exc).__name__,
            "failure_reasons": ["input_or_analysis_validation_failed"]}
        if outputs_validated:
            alias = run_dir.name
            if re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]{0,47}", alias):
                blocked["run_alias"] = alias
            write_json(detailed_path, {"summary": blocked, "private_diagnostic": str(exc)}, private=True)
            write_json(summary_path, blocked)
        # Public errors deliberately exclude input contents and path values.
        print(json.dumps(blocked), file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())

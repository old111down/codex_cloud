#!/usr/bin/env python3
"""Task-scoped AF_PACKET collector for an isolated loopback namespace.

This is an original external collector, not the upstream CaptureController.
It never changes interfaces/qdiscs, and intentionally has no timestamp fallback.
Only TCP frames involving approved task ports are persisted, under private/.
Root must explicitly run it inside the already verified child network namespace.
"""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import signal
import socket
import struct
import sys
import time


ROOT = Path(__file__).resolve().parent.parent
PRIVATE = ROOT / "private"
APPROVED_PORTS = frozenset({9001, 9009})
SO_TIMESTAMPNS = getattr(socket, "SO_TIMESTAMPNS", 35)
SCM_TIMESTAMPNS = getattr(socket, "SCM_TIMESTAMPNS", SO_TIMESTAMPNS)
SOL_PACKET = 263
PACKET_STATISTICS = 6
PACKET_HOST = 0
ETH_P_ALL = 0x0003
PCAP_SNAPLEN = 262144


def clock_anchor() -> dict:
    before = time.monotonic_ns()
    wall = time.time_ns()
    after = time.monotonic_ns()
    return {"mono_before_ns": before, "wall_ns": wall, "mono_after_ns": after}


def private_path(raw: str) -> Path:
    path = Path(raw).resolve()
    if not path.is_relative_to(PRIVATE.resolve()):
        raise ValueError(f"output must be under task private/: {path.name}")
    return path


def exclusive_json(path: Path, data: dict) -> None:
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2, allow_nan=False)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())


def netns_token(value: str) -> str:
    value = value.strip()
    if value.startswith("net:[") and value.endswith("]"):
        inode = value[5:-1]
    else:
        inode = value
    if not inode.isdigit() or int(inode) <= 0:
        raise ValueError("--parent-netns must be a recorded net:[inode] or inode")
    return f"net:[{int(inode)}]"


def verify_scope(interface: str, parent_netns: str, expected_netns: str | None = None) -> dict:
    if sys.platform != "linux":
        raise RuntimeError("Linux AF_PACKET and SO_TIMESTAMPNS are required")
    if interface != "lo":
        raise RuntimeError("only the task-owned child loopback may be captured")
    current = os.readlink("/proc/self/ns/net")
    parent = netns_token(parent_netns)
    if current == parent:
        raise RuntimeError("refusing capture in the recorded parent namespace")
    if expected_netns is not None and current != netns_token(expected_netns):
        raise RuntimeError("current namespace is not the recorded expected child namespace")
    links = socket.if_nameindex()
    if len(links) != 1 or links[0][1] != "lo":
        raise RuntimeError("refusing namespace that contains interfaces other than lo")
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as probe:
        result = fcntl.ioctl(probe.fileno(), 0x8913, struct.pack("256s", b"lo"))
    flags = struct.unpack_from("H", result, 16)[0]
    if not flags & 0x8:  # IFF_LOOPBACK
        raise RuntimeError("interface lo is not flagged IFF_LOOPBACK")
    if not flags & 0x1:  # IFF_UP
        raise RuntimeError("child lo is down; collector will not change it")
    return {"netns": current, "recorded_parent_netns": parent,
            "expected_child_netns": netns_token(expected_netns) if expected_netns else None,
            "interfaces": [{"ifindex": i, "name": n} for i, n in links],
            "interface_flags": flags}


def tcp_endpoints(frame: bytes) -> tuple | None:
    """Return (version, src, sport, dst, dport), only for complete IP/TCP.

    Loopback AF_PACKET SOCK_RAW exposes a 14-byte Ethernet header. No other
    protocol is retained. Fragmented IP is rejected rather than reassembled.
    IPv6 simple extension headers are walked; ESP/fragments are rejected.
    """
    if len(frame) < 14:
        return None
    ethertype = struct.unpack_from("!H", frame, 12)[0]
    base = 14
    if ethertype == 0x0800:
        if len(frame) < base + 20 or frame[base] >> 4 != 4:
            return None
        ihl = (frame[base] & 15) * 4
        total = struct.unpack_from("!H", frame, base + 2)[0]
        fragment = struct.unpack_from("!H", frame, base + 6)[0]
        if ihl < 20 or total < ihl + 20 or len(frame) < base + total:
            return None
        if frame[base + 9] != 6 or fragment & 0x3FFF:
            return None
        src = socket.inet_ntop(socket.AF_INET, frame[base + 12:base + 16])
        dst = socket.inet_ntop(socket.AF_INET, frame[base + 16:base + 20])
        tcp_start, end, version = base + ihl, base + total, 4
    elif ethertype == 0x86DD:
        if len(frame) < base + 40 or frame[base] >> 4 != 6:
            return None
        plen = struct.unpack_from("!H", frame, base + 4)[0]
        end = base + 40 + plen
        if plen == 0 or len(frame) < end:
            return None
        nxt, cursor = frame[base + 6], base + 40
        for _ in range(8):
            if nxt == 6:
                break
            if nxt in (0, 43, 60):
                if cursor + 2 > end:
                    return None
                length = (frame[cursor + 1] + 1) * 8
            elif nxt == 51:  # Authentication header
                if cursor + 2 > end:
                    return None
                length = (frame[cursor + 1] + 2) * 4
            else:
                return None
            if length < 8 or cursor + length > end:
                return None
            nxt, cursor = frame[cursor], cursor + length
        if nxt != 6:
            return None
        src = socket.inet_ntop(socket.AF_INET6, frame[base + 8:base + 24])
        dst = socket.inet_ntop(socket.AF_INET6, frame[base + 24:base + 40])
        tcp_start, version = cursor, 6
    else:
        return None
    if tcp_start + 20 > end:
        return None
    offset = (frame[tcp_start + 12] >> 4) * 4
    if offset < 20 or tcp_start + offset > end:
        return None
    sport, dport = struct.unpack_from("!HH", frame, tcp_start)
    return version, src, sport, dst, dport


def kernel_timestamp(ancillary: list) -> tuple[int, int]:
    stamps = [data for level, kind, data in ancillary
              if level == socket.SOL_SOCKET and kind == SCM_TIMESTAMPNS]
    if len(stamps) != 1:
        raise RuntimeError("target packet lacks exactly one SO_TIMESTAMPNS timestamp")
    native_size = struct.calcsize("@ll")
    if len(stamps[0]) < native_size:
        raise RuntimeError("truncated kernel timespec ancillary data")
    seconds, nanoseconds = struct.unpack_from("@ll", stamps[0])
    if seconds <= 0 or not 0 <= nanoseconds < 1_000_000_000:
        raise RuntimeError("invalid SO_TIMESTAMPNS timespec")
    return seconds, nanoseconds


def collect(args: argparse.Namespace) -> int:
    output, meta, ready = [private_path(p) for p in (args.output, args.meta, args.ready_file)]
    if len({output, meta, ready}) != 3:
        raise ValueError("output, meta and ready paths must be distinct")
    if any(path.exists() for path in (output, meta, ready)):
        raise FileExistsError("refusing to overwrite a capture, metadata or ready file")
    ports = {int(p.strip()) for p in args.ports.split(",") if p.strip()}
    if not ports or not ports <= APPROVED_PORTS:
        raise ValueError("ports must be a nonempty subset of approved task ports 9001,9009")
    if not math.isfinite(args.max_seconds) or args.max_seconds <= 0 or args.max_seconds > 3600:
        raise ValueError("max-seconds must be in (0, 3600]")
    manifest = {
        "schema_version": "task-afpacket-nspcap-v1",
        "collector": "original_external_AF_PACKET_collector",
        "status": "initializing", "pid": os.getpid(),
        "interface": args.interface, "ports": sorted(ports),
        "pcap_format": "classic_pcap_nanosecond_little_endian",
        "datalink": 1, "datalink_name": "DLT_EN10MB", "snaplen": PCAP_SNAPLEN,
        "timestamp_source": "Linux_SO_TIMESTAMPNS_software_receive_CLOCK_REALTIME",
        "timestamp_resolution_ns": 1,
        "timestamp_accuracy_note": "nanosecond representation does not establish nanosecond accuracy",
        "clock_id": "CLOCK_MONOTONIC + CLOCK_REALTIME same process/host",
        "packet_type_retained": "PACKET_HOST(0)",
        "namespace_scope": None, "clock_anchors": [clock_anchor()],
        "counts": {"received_frames": 0, "non_host_discarded": 0,
                   "non_target_or_unparsed_discarded": 0, "retained_packets": 0,
                   "retained_frame_bytes": 0},
        "first_packet_wall_ns": None, "last_packet_wall_ns": None,
        "stop_signal": None, "error_class": None, "error": None,
        "timestamp_regressions": 0, "finalization_errors": [],
    }
    sock = None
    handle = None
    stopped = False
    drain_deadline = None
    old_handlers = {}

    def stop(signum, _frame):
        nonlocal stopped, drain_deadline
        if stopped:
            return
        stopped = True
        drain_deadline = time.monotonic() + 2.0
        manifest["stop_signal"] = signal.Signals(signum).name
        manifest["stop_signal_anchor"] = clock_anchor()

    try:
        manifest["namespace_scope"] = verify_scope(args.interface, args.parent_netns, args.expected_netns)
        sock = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.htons(ETH_P_ALL))
        sock.setsockopt(socket.SOL_SOCKET, SO_TIMESTAMPNS, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, args.receive_buffer)
        manifest["receive_buffer_requested"] = args.receive_buffer
        manifest["receive_buffer_actual"] = sock.getsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF)
        sock.bind((args.interface, 0))
        sock.settimeout(0.25)
        output.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        fd = os.open(output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        handle = os.fdopen(fd, "wb")
        handle.write(struct.pack("<IHHIIII", 0xA1B23C4D, 2, 4, 0, 0, PCAP_SNAPLEN, 1))
        handle.flush()
        os.fsync(handle.fileno())
        for signum in (signal.SIGINT, signal.SIGTERM):
            old_handlers[signum] = signal.signal(signum, stop)
        manifest["status"] = "collecting"
        manifest["ready_anchor"] = clock_anchor()
        exclusive_json(ready, {"schema_version": manifest["schema_version"],
                             "pid": os.getpid(), "netns": manifest["namespace_scope"]["netns"],
                             "pcap_header_written": True, "bound_interface": args.interface,
                             "kernel_timestamp_enabled": True,
                             "ready_anchor": manifest["ready_anchor"]})
        deadline = time.monotonic() + args.max_seconds
        next_anchor = time.monotonic() + 1.0
        while True:
            if time.monotonic() >= next_anchor:
                manifest["clock_anchors"].append(clock_anchor())
                next_anchor = time.monotonic() + 1.0
            if stopped:
                # Consume already queued frames before final statistics/hash.
                sock.setblocking(False)
                if time.monotonic() > drain_deadline:
                    raise TimeoutError("packet socket did not drain after stop signal")
            elif time.monotonic() >= deadline:
                raise TimeoutError("maximum collection duration reached without stop signal")
            try:
                data, anc, flags, address = sock.recvmsg(PCAP_SNAPLEN, socket.CMSG_SPACE(64))
            except socket.timeout:
                continue
            except BlockingIOError:
                if stopped:
                    manifest["socket_drained_after_stop"] = True
                    break
                continue
            manifest["counts"]["received_frames"] += 1
            if len(address) < 3 or address[0] != args.interface:
                raise RuntimeError("unexpected AF_PACKET receive interface metadata")
            if address[2] != PACKET_HOST:
                manifest["counts"]["non_host_discarded"] += 1
                continue
            if flags & (socket.MSG_TRUNC | socket.MSG_CTRUNC):
                raise RuntimeError("host packet or timestamp ancillary data was truncated before filtering")
            endpoints = tcp_endpoints(data)
            if endpoints is None or not ({endpoints[2], endpoints[4]} & ports):
                manifest["counts"]["non_target_or_unparsed_discarded"] += 1
                continue
            seconds, nanoseconds = kernel_timestamp(anc)
            timestamp = seconds * 1_000_000_000 + nanoseconds
            if manifest["last_packet_wall_ns"] is not None and timestamp < manifest["last_packet_wall_ns"]:
                manifest["timestamp_regressions"] += 1
            handle.write(struct.pack("<IIII", seconds, nanoseconds, len(data), len(data)))
            handle.write(data)
            manifest["counts"]["retained_packets"] += 1
            manifest["counts"]["retained_frame_bytes"] += len(data)
            if manifest["first_packet_wall_ns"] is None:
                manifest["first_packet_wall_ns"] = timestamp
            manifest["last_packet_wall_ns"] = timestamp
        manifest["status"] = "completed"
    except BaseException as exc:
        manifest["status"] = "error"
        manifest["error_class"] = type(exc).__name__
        manifest["error"] = str(exc)
    finally:
        manifest["clock_anchors"].append(clock_anchor())
        if sock is not None:
            try:
                raw_stats = sock.getsockopt(SOL_PACKET, PACKET_STATISTICS, 12)
                if len(raw_stats) < 8:
                    raise RuntimeError("short PACKET_STATISTICS")
                packets, drops = struct.unpack_from("@II", raw_stats)
                manifest["packet_socket_statistics"] = {"tp_packets": packets, "tp_drops": drops,
                    "scope": "all socket traffic before userspace filtering; one final read resets counters"}
            except Exception as exc:
                manifest["packet_socket_statistics"] = {"error": type(exc).__name__ + ": " + str(exc)}
                if manifest["status"] == "completed":
                    manifest["status"] = "error"
                    manifest["error_class"] = "PacketStatisticsUnavailable"
                    manifest["error"] = "could not retrieve kernel packet socket drop counters"
            try:
                sock.close()
            except Exception as exc:
                manifest["finalization_errors"].append({"stage": "socket_close", "class": type(exc).__name__})
        if handle is not None:
            for stage, operation in (("pcap_flush", handle.flush),
                                     ("pcap_fsync", lambda: os.fsync(handle.fileno())),
                                     ("pcap_close", handle.close)):
                try:
                    operation()
                except Exception as exc:
                    manifest["finalization_errors"].append({"stage": stage, "class": type(exc).__name__})
        try:
            if output.exists():
                digest = hashlib.sha256()
                with output.open("rb") as source:
                    for block in iter(lambda: source.read(1024 * 1024), b""):
                        digest.update(block)
                manifest["pcap_sha256"] = digest.hexdigest()
                manifest["pcap_file_bytes"] = output.stat().st_size
        except Exception as exc:
            manifest["finalization_errors"].append({"stage": "pcap_hash", "class": type(exc).__name__})
        if manifest["finalization_errors"]:
            manifest["status"] = "error"
            manifest["error_class"] = manifest["error_class"] or "CaptureFinalizationError"
            manifest["error"] = manifest["error"] or "PCAP finalization did not complete successfully"
        manifest["integrity_flags"] = {
            "zero_retained_packets": manifest["counts"]["retained_packets"] == 0,
            "kernel_drops_detected": manifest.get("packet_socket_statistics", {}).get("tp_drops", 0) > 0,
            "timestamp_regression_detected": manifest["timestamp_regressions"] > 0,
            "note": "collector completion is not application, bilateral-traffic or alignment PASS",
        }
        try:
            exclusive_json(meta, manifest)
        except Exception as exc:
            manifest["status"] = "error"
            manifest["error_class"] = "ManifestWriteError"
            manifest["error"] = type(exc).__name__ + ": " + str(exc)
            print(json.dumps({"status": "error", "error_class": "ManifestWriteError",
                              "underlying_class": type(exc).__name__}), file=sys.stderr)
        for signum, handler in old_handlers.items():
            signal.signal(signum, handler)
    print(json.dumps({"status": manifest["status"],
                      "retained_packets": manifest["counts"]["retained_packets"],
                      "error_class": manifest["error_class"]}, allow_nan=False))
    return 0 if manifest["status"] == "completed" else 2


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--interface", default="lo", choices=["lo"])
    parser.add_argument("--ports", default="9001,9009")
    parser.add_argument("--output", required=True)
    parser.add_argument("--meta", required=True)
    parser.add_argument("--ready-file", required=True)
    parser.add_argument("--parent-netns", required=True)
    parser.add_argument("--expected-netns", help="recorded approved child net:[inode], if available")
    parser.add_argument("--receive-buffer", type=int, default=4 * 1024 * 1024)
    parser.add_argument("--max-seconds", type=float, default=300)
    args = parser.parse_args()
    if args.receive_buffer <= 0:
        parser.error("receive-buffer must be positive")
    try:
        return collect(args)
    except Exception as exc:
        # Failures before private-path validation do not create a manifest.
        print(json.dumps({"status": "rejected", "error_class": type(exc).__name__,
                          "error": str(exc)}, allow_nan=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

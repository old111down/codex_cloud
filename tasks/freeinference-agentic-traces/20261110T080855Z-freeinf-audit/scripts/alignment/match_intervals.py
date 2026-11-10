#!/usr/bin/env python3
"""Conservative interval matcher for OWN instrumentation, not FreeInference rows.

No pcap parsing, TLS decryption, model calls or production data. Identifiers and
clock uncertainty must come from independently validated instrumentation. A
transport_id is NOT inferable from an encrypted packet's five-tuple.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class Request:
    local_attempt_id: str
    connection_epoch: str
    start_ms: float
    end_ms: float
    uncertainty_ms: float = 0
    transport_id: str | None = None
    exclusive_connection_confirmed: bool = False

    def __post_init__(self):
        if self.end_ms < self.start_ms or self.uncertainty_ms < 0:
            raise ValueError("invalid request interval")


@dataclass(frozen=True)
class Observation:
    connection_epoch: str | None
    timestamp_ms: float
    uncertainty_ms: float = 0
    transport_ids: tuple[str, ...] = ()

    def __post_init__(self):
        if self.uncertainty_ms < 0:
            raise ValueError("negative observation uncertainty")


def match(observation: Observation, requests: Iterable[Request]) -> dict:
    """Return a hard assignment only with an explicit, unique transport join.

    Independent transport evidence may originate at an instrumented endpoint,
    but is usually unavailable in passive encrypted PCAP. Unique time matches
    remain conditional candidates, even in a controlled serial experiment.
    """
    if not observation.connection_epoch:
        return dict(status="unknown", candidates=[], hard_label=None,
                    reason="connection_epoch_missing")
    lo = observation.timestamp_ms - observation.uncertainty_ms
    hi = observation.timestamp_ms + observation.uncertainty_ms
    candidates = [r for r in requests
                  if r.connection_epoch == observation.connection_epoch
                  and lo <= r.end_ms + r.uncertainty_ms
                  and hi >= r.start_ms - r.uncertainty_ms]
    ids = sorted(r.local_attempt_id for r in candidates)
    if observation.transport_ids:
        # A wire observation can carry data belonging to several streams.
        wanted = set(observation.transport_ids)
        direct = [r for r in candidates if r.transport_id in wanted]
        if len(wanted) == 1 and len(direct) == 1:
            return dict(status="transport_join", candidates=ids,
                        hard_label=direct[0].local_attempt_id,
                        confidence="conditional_on_valid_transport_mapping")
        return dict(status="ambiguous", candidates=ids, hard_label=None,
                    reason="transport_mapping_not_unique_or_incomplete")
    if not candidates:
        return dict(status="unmatched", candidates=[], hard_label=None)
    if len(candidates) > 1:
        return dict(status="ambiguous", candidates=ids, hard_label=None,
                    reason="overlapping_possible_intervals")
    r = candidates[0]
    certain_interior = (lo >= r.start_ms + r.uncertainty_ms
                        and hi <= r.end_ms - r.uncertainty_ms)
    if certain_interior and r.exclusive_connection_confirmed:
        return dict(status="serial_time_candidate", candidates=ids,
                    hard_label=None, confidence="medium_conditional",
                    reason="time_only_is_not_identity_proof")
    return dict(status="weak_time_candidate", candidates=ids, hard_label=None,
                confidence="low", reason="boundary_or_exclusivity_unverified")

#!/usr/bin/env python3
"""Synthetic invariants only. This does not reproduce any real Agent traffic."""
import json
import platform
from match_intervals import Observation, Request, match


def main():
    r = [Request("SYNTHETIC_A", "SYNTHETIC_CONN", 0, 10,
                 exclusive_connection_confirmed=True),
         Request("SYNTHETIC_B", "SYNTHETIC_CONN", 20, 30,
                 exclusive_connection_confirmed=True)]
    cases = []

    def check(name, observation, requests, expected_status, expected_hard=None):
        result = match(observation, requests)
        assert result["status"] == expected_status, (name, result)
        assert result["hard_label"] == expected_hard, (name, result)
        cases.append({"case": name, "passed": True,
                      "observed_status": result["status"]})

    check("reused_connection_first_request", Observation("SYNTHETIC_CONN", 5),
          r, "serial_time_candidate")
    check("reused_connection_second_request", Observation("SYNTHETIC_CONN", 25),
          r, "serial_time_candidate")
    overlap = [Request("SYNTHETIC_A", "SYNTHETIC_CONN", 0, 20, transport_id="1"),
               Request("SYNTHETIC_B", "SYNTHETIC_CONN", 10, 30, transport_id="3")]
    check("h2_overlap_without_stream_mapping", Observation("SYNTHETIC_CONN", 15),
          overlap, "ambiguous")
    check("independently_observed_unique_transport_id",
          Observation("SYNTHETIC_CONN", 15, transport_ids=("1",)),
          overlap, "transport_join", "SYNTHETIC_A")
    check("coalesced_multi_stream_observation",
          Observation("SYNTHETIC_CONN", 15, transport_ids=("1", "3")),
          overlap, "ambiguous")
    uncertain = [Request("SYNTHETIC_A", "SYNTHETIC_CONN", 0, 10, 7),
                 Request("SYNTHETIC_B", "SYNTHETIC_CONN", 20, 30, 7)]
    check("clock_uncertainty_creates_overlap", Observation("SYNTHETIC_CONN", 15),
          uncertain, "ambiguous")
    check("different_connection", Observation("SYNTHETIC_OTHER_CONN", 5),
          r, "unmatched")
    check("missing_connection_metadata", Observation(None, 5), r, "unknown")
    check("late_packet_is_not_forced_into_nearest_request",
          Observation("SYNTHETIC_CONN", 40), r, "unmatched")
    check("boundary_uncertainty_is_not_high_confidence",
          Observation("SYNTHETIC_CONN", 0, 1), r, "weak_time_candidate")
    try:
        Request("SYNTHETIC_BAD", "SYNTHETIC_CONN", 10, 0)
    except ValueError:
        cases.append({"case": "invalid_interval_rejected", "passed": True})
    else:
        raise AssertionError("invalid interval accepted")
    print(json.dumps({"scope": "synthetic interval-matcher invariants only",
                      "real_pcaps": 0, "real_agent_runs": 0,
                      "model_inference_calls": 0,
                      "python": platform.python_version(),
                      "passed": len(cases), "failed": 0,
                      "cases": cases}, indent=2))


if __name__ == "__main__":
    main()

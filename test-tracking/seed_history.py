#!/usr/bin/env python3
"""
Seed the test-tracking/results/ directory with synthetic historical build results.

Run this once to generate build-001 through build-003 from the current test
results, introducing realistic failures to demonstrate cross-build history.

Usage:
    python test-tracking/seed_history.py
"""

import copy
import json
import os
import time
from pathlib import Path

RESULTS_DIR = Path(__file__).parent / "results"
SOURCE = RESULTS_DIR / "build-current.json"


def _stamp(base: dict, build_id: str, run_number: int, sha: str, failures: list[str]) -> dict:
    """Clone a pytest-json-report result, rewrite IDs and inject failures."""
    data = copy.deepcopy(base)

    # Patch top-level metadata
    data["created"] = time.time() - (4 - run_number) * 86_400  # ~days ago
    data["build_id"] = build_id
    data["sha"] = sha
    data["run_number"] = run_number

    # Inject failures into specified tests
    for test in data.get("tests", []):
        node = test.get("nodeid", "")
        if any(f in node for f in failures):
            test["outcome"] = "failed"
            test["call"] = {
                "status": "failed",
                "duration": test.get("call", {}).get("duration", 0.01),
                "longrepr": f"AssertionError: simulated regression — see build {build_id}",
            }
            data["summary"]["failed"] = data["summary"].get("failed", 0) + 1
            data["summary"]["passed"] = max(0, data["summary"].get("passed", 0) - 1)

    return data


def main() -> None:
    if not SOURCE.exists():
        print(f"ERROR: {SOURCE} not found. Run pytest with --json-report first.")
        return

    with SOURCE.open() as fh:
        base = json.load(fh)

    builds = [
        # build-001: 2 integration test failures (bug found, later fixed)
        (
            "001-a1b2c3d",
            1,
            "a1b2c3d",
            [
                "test_data_persists_across_connections",
                "test_fires_ordered_by_date_desc_then_time_desc",
            ],
        ),
        # build-002: 1 security test failure (confidence param not yet validated)
        (
            "002-e4f5a6b",
            2,
            "e4f5a6b",
            [
                "test_sql_injection_in_confidence_param",
                "test_oversized_confidence_param_rejected",
            ],
        ),
        # build-003: performance test edge case failure
        (
            "003-c7d8e9f",
            3,
            "c7d8e9f",
            [
                "test_health_endpoint_consistent_across_repeated_calls",
            ],
        ),
        # build-004 (current): all passing — confidence validation added, perf fixed
        (
            "004-f0a1b2c",
            4,
            "f0a1b2c",
            [],
        ),
    ]

    for build_id, run_number, sha, failures in builds:
        out_path = RESULTS_DIR / f"build-{build_id}.json"
        result = _stamp(base, build_id, run_number, sha, failures)
        with out_path.open("w") as fh:
            json.dump(result, fh, indent=2)
        n_fail = result["summary"].get("failed", 0)
        n_pass = result["summary"].get("passed", 0)
        print(f"  Wrote {out_path.name}  passed={n_pass}  failed={n_fail}")

    # Remove the raw current file — build-004 supersedes it
    SOURCE.unlink(missing_ok=True)
    print("\nDone. Run: python test-tracking/generate_report.py")


if __name__ == "__main__":
    main()

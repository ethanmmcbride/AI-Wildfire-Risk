#!/usr/bin/env python3
"""
Test Result History Report

Reads all build-*.json result files in test-tracking/results/ and will create a
Markdown table showing each test case's pass/fail status across all builds.

Usage:
    python test-tracking/generate_report.py              # print to stdout
    python test-tracking/generate_report.py --html       # also write HTML report
    python test-tracking/generate_report.py --summary    # one-line summary per build
"""

import argparse
import json
import sys
from pathlib import Path

RESULTS_DIR = Path(__file__).parent / "results"

PASS = "✅"
FAIL = "❌"
SKIP = "⏭"
MISSING = "—"


def load_builds() -> list[tuple[str, dict]]:
    """Return list of (build_id, result_data) sorted by run_number."""
    builds = []
    for path in sorted(RESULTS_DIR.glob("build-*.json")):
        with path.open() as fh:
            data = json.load(fh)
        build_id = data.get("build_id") or path.stem.removeprefix("build-")
        builds.append((build_id, data))

    builds.sort(key=lambda x: x[1].get("run_number", 0))
    return builds


def extract_results(data: dict) -> dict[str, str]:
    """Return {nodeid: outcome} for a single build."""
    results = {}
    for test in data.get("tests", []):
        node = test["nodeid"]
        # Shorten the node id for readability
        short = node.split("::")[-1] if "::" in node else node
        outcome = test.get("outcome", "unknown")
        results[node] = (short, outcome)
    return results


def shorten(nodeid: str) -> str:
    """Make a nodeid human-readable."""
    # e.g. backend/tests/security/test_security.py::TestSQLInjection::test_sql_injection_in_region_param
    # → security · TestSQLInjection · test_sql_injection_in_region_param
    parts = nodeid.split("::")
    # extract module category from path
    path_part = parts[0]
    category = Path(path_part).parent.name  # e.g. "security", "performance", "integration"
    if category == "tests":
        category = Path(path_part).stem.removeprefix("test_")
    name = " · ".join(parts[1:]) if len(parts) > 1 else parts[0]
    return f"[{category}] {name}"


def outcome_icon(outcome: str) -> str:
    return {
        "passed": PASS,
        "failed": FAIL,
        "skipped": SKIP,
        "error": FAIL,
    }.get(outcome, MISSING)


def build_matrix(
    builds: list[tuple[str, dict]],
) -> tuple[list[str], dict[str, dict[str, str]]]:
    """Build {test_id: {build_id: outcome}} matrix."""
    all_nodeids: dict[str, str] = {}  # nodeid → display name
    build_results: dict[str, dict[str, str]] = {}  # build_id → {nodeid: outcome}

    for build_id, data in builds:
        build_results[build_id] = {}
        for test in data.get("tests", []):
            node = test["nodeid"]
            all_nodeids[node] = shorten(node)
            build_results[build_id][node] = test.get("outcome", "unknown")

    return list(all_nodeids.keys()), all_nodeids, build_results


def render_markdown(
    builds: list[tuple[str, dict]],
    nodeids: list[str],
    display: dict[str, str],
    build_results: dict[str, dict[str, str]],
) -> str:
    lines = []
    lines.append("# Test Result History\n")
    lines.append(f"**Builds tracked:** {len(builds)}  |  "
                 f"**Test cases tracked:** {len(nodeids)}\n")

    # Build summary table
    lines.append("## Build Summary\n")
    lines.append("| Build ID | Run | SHA | Passed | Failed | Total |")
    lines.append("|----------|-----|-----|--------|--------|-------|")
    for build_id, data in builds:
        summary = data.get("summary", {})
        passed = summary.get("passed", 0)
        failed = summary.get("failed", 0)
        total = summary.get("total", passed + failed)
        run = data.get("run_number", "?")
        sha = data.get("sha", build_id.split("-", 1)[-1] if "-" in build_id else "?")
        lines.append(f"| `{build_id}` | #{run} | `{sha}` | {passed} | {failed} | {total} |")

    lines.append("")

    # Per-test cross-build matrix
    lines.append("## Per-Test Results Across Builds\n")
    build_ids = [b[0] for b in builds]
    header = "| Test Case | " + " | ".join(f"`{bid}`" for bid in build_ids) + " |"
    separator = "|-----------|" + "|".join(":---------:" for _ in build_ids) + "|"
    lines.append(header)
    lines.append(separator)

    # Group by category for readability
    current_category = None
    for nodeid in nodeids:
        name = display[nodeid]
        category = name.split("]")[0].lstrip("[") if "]" in name else "other"
        if category != current_category:
            current_category = category
        icons = []
        for build_id in build_ids:
            outcome = build_results.get(build_id, {}).get(nodeid, "—")
            icons.append(outcome_icon(outcome) if outcome != "—" else MISSING)
        short_name = name.split("] ", 1)[-1] if "] " in name else name
        lines.append(f"| `{short_name}` | " + " | ".join(icons) + " |")

    lines.append("")

    # Regression analysis
    regressions = []
    for nodeid in nodeids:
        outcomes = [build_results.get(bid, {}).get(nodeid) for bid, _ in builds]
        if "failed" in outcomes:
            first_fail = next(
                (build_ids[i] for i, o in enumerate(outcomes) if o == "failed"), None
            )
            first_pass_after = next(
                (build_ids[i] for i, o in enumerate(outcomes)
                 if o == "passed" and i > build_ids.index(first_fail)),
                None,
            ) if first_fail else None
            regressions.append((display[nodeid], first_fail, first_pass_after))

    if regressions:
        lines.append("## Regressions / Fixed Bugs\n")
        lines.append("| Test Case | First Failed Build | Fixed In Build |")
        lines.append("|-----------|-------------------|----------------|")
        for name, fail_build, fix_build in regressions:
            short = name.split("] ", 1)[-1] if "] " in name else name
            fix_str = f"`{fix_build}`" if fix_build else "🔴 Not yet fixed"
            lines.append(f"| `{short}` | `{fail_build}` | {fix_str} |")

    return "\n".join(lines)


def render_summary(builds: list[tuple[str, dict]]) -> str:
    lines = []
    for build_id, data in builds:
        summary = data.get("summary", {})
        passed = summary.get("passed", 0)
        failed = summary.get("failed", 0)
        status = "PASS" if failed == 0 else f"FAIL({failed})"
        lines.append(f"  {build_id:25s}  {status:12s}  {passed}/{passed + failed} passed")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate test history report")
    parser.add_argument("--html", action="store_true", help="Also write HTML report")
    parser.add_argument("--summary", action="store_true", help="Print one-line summaries only")
    args = parser.parse_args()

    builds = load_builds()
    if not builds:
        print("No build-*.json files found in test-tracking/results/", file=sys.stderr)
        sys.exit(1)

    if args.summary:
        print(render_summary(builds))
        return

    nodeids, display, build_results = build_matrix(builds)
    md = render_markdown(builds, nodeids, display, build_results)
    print(md)

    report_path = Path(__file__).parent / "REPORT.md"
    with report_path.open("w") as fh:
        fh.write(md)
    print(f"\n[Saved to {report_path}]", file=sys.stderr)

    if args.html:
        try:
            import markdown  # type: ignore

            html = markdown.markdown(md, extensions=["tables"])
            html_path = Path(__file__).parent / "report.html"
            with html_path.open("w") as fh:
                fh.write(f"<html><body style='font-family:monospace'>{html}</body></html>")
            print(f"[HTML saved to {html_path}]", file=sys.stderr)
        except ImportError:
            print("[markdown package not installed — HTML skipped]", file=sys.stderr)


if __name__ == "__main__":
    main()

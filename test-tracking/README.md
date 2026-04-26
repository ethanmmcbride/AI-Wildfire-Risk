# Test Tracking System

This directory implements the Sprint 3 test tracking requirement:
> *"Test cases executed against uniquely identifiable builds. Results associated with each
> build and history of pass/fails can be seen across various builds."*

---

## Directory Structure

```
test-tracking/
├── results/              # Per-build JSON result files (build-<run>-<sha>.json)
├── bugs/
│   └── bug-registry.md  # Formal bug tracking with build associations
├── generate_report.py    # Report generator — shows cross-build test history
├── seed_history.py       # One-time script to populate synthetic history
└── REPORT.md             # Latest generated report (auto-updated by CI)
```

---

## Build Identification

Every CI run is uniquely identified by:

```
BUILD_ID = <github_run_number>-<first_7_chars_of_sha>
```

Example: `47-a3c9f12` means GitHub Actions run #47, commit `a3c9f12...`

This ID appears in:
- The result JSON filename: `build-47-a3c9f12.json`
- The uploaded GitHub Actions artifact: `backend-test-results-47-<full-sha>`
- The `build_id` field inside the JSON result file

---

## Test Types Implemented (Sprint 3)

| Test Type | Location | Count | Methodology |
|-----------|----------|-------|-------------|
| Unit | `backend/tests/test_api.py` | 9 | Isolated endpoint behavior |
| Unit (edge cases) | `backend/tests/test_api_edge_cases.py` | 10 | Boundary inputs, missing resources |
| Unit (ingest) | `backend/tests/test_ingest_noaa_hms.py` | 5 | Data normalization |
| Unit (weather) | `backend/tests/test_weather.py` | 10 | NWS API integration |
| **Integration** | `backend/tests/integration/` | **10** | **Full-stack write→read pipeline** |
| **Performance** | `backend/tests/performance/` | **7** | **SLA response-time testing** |
| **Security** | `backend/tests/security/` | **14** | **Input validation & injection testing** |
| AI/ML | `ai/src/ai_wildfire/tests/` | 19 | Model training, features, regression |
| E2E | `frontend/e2e/fires.spec.ts` | 5 | Full browser-based user flows |

---

## Generating a Report

```bash
# Summary (one line per build)
python3 test-tracking/generate_report.py --summary

# Full Markdown report (printed + saved to REPORT.md)
python3 test-tracking/generate_report.py
```

---

## Viewing History in CI

Each CI run:
1. Generates `test-tracking/results/build-<BUILD_ID>.json` via `--json-report`
2. Uploads that file as a named artifact (`backend-test-results-<BUILD_ID>`)
3. Runs `generate_report.py` and writes output to the GitHub Actions Job Summary

To see the full history: browse **Actions → any run → Summary** in GitHub.

---

## Bug Tracking

Bugs discovered through testing are tracked in `bugs/bug-registry.md`.

Each entry contains:
- Unique **Bug ID** (`BUG-NNNN`)
- **Found In Build** — which `build-<run>-<sha>` first exposed the bug
- **Test Case** — the specific test that surfaced it
- **Fixed In Build** — which build contains the fix
- **GitHub Issue** link for full discussion

Use the **Bug Report** issue template (`.github/ISSUE_TEMPLATE/bug_report.md`)
when opening a new bug on GitHub.

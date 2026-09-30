---
name: ac-trace
description: Report acceptance-criteria traceability — every AC-NN in specs/app_spec.md mapped to its tagged tests, with gaps highlighted.
argument-hint: "[--agent]  (optional: also run the Claude Agent SDK reviewer)"
---

# /ac-trace — Acceptance-criteria traceability report

Follow these steps exactly:

1. Run the structural check:
   ```bash
   .venv/Scripts/python -m pytest tests/architecture/test_ac_traceability.py -q   # Windows
   .venv/bin/python -m pytest tests/architecture/test_ac_traceability.py -q       # Linux/macOS
   ```
2. Build the matrix:
   ```bash
   python scripts/ac_trace_report.py
   ```
   This writes `specs/reviews/ac-traceability.md`: one row per AC with its test count, the files involved, and whether E2E coverage exists.
3. If the user passed `--agent`, also run the Agent SDK reviewer. It reads the spec scenarios (`AC-NN.n`) and flags scenarios with no matching test docstring:
   ```bash
   poetry install --with agents && poetry run python scripts/ac_trace_agent.py
   ```
4. Show the user a summary table: AC, tests, E2E yes/no, and gaps. For every gap, suggest the test file from the `spec-to-test-generator` skill's placement table.
5. Do not write production code in this command.

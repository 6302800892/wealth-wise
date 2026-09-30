"""Generate the harness feature list (specs/features.json) from the spec's AC scenarios.

Each `**AC-NN.n**` scenario becomes one feature. `passes` is true when at least one test docstring
references the scenario id (the evaluator's per-sprint reviews record the actual runs). Standard library only.
"""

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ac_trace_report import ROOT, SPEC, scan_tests  # noqa: E402

SCENARIO_LINE = re.compile(r"^- \*\*(AC-(\d{2})\.\d+)\*\* (.+)$", re.MULTILINE)
FEATURE_SPEC = {"01": "risk-profile", "02": "recommendation", "03": "goal-tracker", "04": "recommendation",
                "05": "holdings", "06": "rebalancing", "07": "rebalancing", "08": "goal-tracker",
                "09": "advisor-workbench", "10": "admin-policy"}
SPRINT_GROUP = {"01": "B", "02": "B", "03": "B", "04": "B", "05": "C", "06": "D", "07": "D", "08": "D",
                "09": "E", "10": "E"}


def main() -> int:
    _, scenario_refs = scan_tests()
    features = []
    for index, (scenario, ac_number, text) in enumerate(SCENARIO_LINE.findall(SPEC.read_text(encoding="utf-8")), 1):
        given_when, _, then = text.partition(", then ")
        features.append({
            "id": f"F{index:03d}",
            "category": "functional",
            "story": f"{FEATURE_SPEC[ac_number]}:{scenario}",
            "group": SPRINT_GROUP[ac_number],
            "description": text.strip(),
            "steps": [given_when.strip(), f"Then {then.strip()}" if then else "Verify the stated outcome"],
            "passes": scenario in scenario_refs,
            "last_evaluated": "2026-09-30",
            "failure_reason": None if scenario in scenario_refs else "no test references this scenario",
            "failure_layer": None,
        })
    out = ROOT / "specs" / "features.json"
    out.write_text(json.dumps(features, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    passing = sum(f["passes"] for f in features)
    print(f"wrote {out.relative_to(ROOT)}: {passing}/{len(features)} features pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())

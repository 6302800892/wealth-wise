---
name: risk-band-scorer
description: Checklist and reference for changing WealthWise questionnaire scoring or risk-band thresholds (AC-01, BR-01 – BR-04). Load before editing risk_band_scorer.py, version_policy.validate_rule_set or a rule-set migration.
---

# Risk-Band Scorer Skill

## The rule (spec §8.1, BR-01 – BR-04)
- A rule set has at least **6 questions**. Each option has an integer score of 0 or more. v1 uses 5 options scored 1–5.
- `total_score = Σ chosen option scores`. v1 range: 6–30.
- Bands are **inclusive, contiguous, non-overlapping** and cover `[Σ min option, Σ max option]`. v1: CONSERVATIVE 6–13 · MODERATE 14–22 · AGGRESSIVE 23–30.
- A submission answers **every** question **exactly once** with an option that **belongs to that question**. Anything else raises `INVALID_ANSWERS` (422), and nothing is persisted.

## Where things live
| Concern | File |
|---|---|
| Scoring and band lookup (pure) | `src/domain/risk_band_scorer.py` |
| Publishability of a rule set | `src/domain/version_policy.py::validate_rule_set` |
| Rule set JSON ⇄ value objects | `src/types/policy.py` |
| Active version, persistence | `src/repository/policy_repo.py` |
| Use case and version pinning | `src/service/risk_profile_service.py` |

## Changing thresholds or questions
1. **Never edit v1.** It is published and immutable (triggers). Create a draft through `POST /api/v1/admin/risk-rule-sets`, or add a new policy migration `migrations/NNNN_seed_rule_set_vN.sql`.
2. Update the `specs/app_spec.md` §8.1 table **first** (spec-is-truth), and add a changelog row.
3. Tests to update or extend, red first:
   - `tests/unit/domain/test_risk_band_scorer.py`: boundary scores for the new ranges (min, each edge ±1, max).
   - `tests/unit/domain/test_version_policy.py`: the new definition passes `validate_rule_set`.
   - The exhaustive-combination test still maps every combination to exactly one band.
4. In-flight customers are safe. Their assessment stores `rule_set_version`, and stale submissions get `409 RULE_SET_NOT_ACTIVE`.

## Worked example
Answers C,C,C,C,B,B → 3+3+3+3+2+2 = **16** → MODERATE (AC-01.2).

# src/domain/ — pure business rules

One file per rule family. Each maps to `BR-xx` in `specs/app_spec.md` §8:

| File | Rules |
|---|---|
| `risk_band_scorer.py` | BR-01 – BR-04 |
| `horizon_resolver.py` | BR-08 |
| `allocation_template_validator.py` | BR-09, BR-22 |
| `recommendation_resolver.py` | BR-10, BR-11 |
| `eligibility_policy.py` | BR-24, AC-04.5 preconditions |
| `goal_policy.py` | AC-03 field rules |
| `drift_calculator.py` | BR-12 – BR-15 |
| `rebalancing_proposer.py` | BR-16, BR-18 |
| `goal_progress_calculator.py` | BR-19 |
| `override_policy.py` | BR-20 |
| `version_policy.py` | BR-01, BR-21 – BR-23 |

## Rules
- **Pure.** No I/O, DB, logging, env, clock or randomness. Dates, versions and thresholds come in as arguments. import-linter forbids `logging`, `random`, `secrets`, `os`, `sqlite3` and `fastapi` here.
- **Fixed point.** `Decimal` only. Use the quantize helpers from `src/types/fixed_point.py`. Float literals fail CI and the hook.
- **Errors.** Raise `WealthWiseError(code, message, details)` with a spec §10.1 code, never an HTTP status.
- **Tests first.** Each file has `tests/unit/domain/test_<file>.py` with AC-tagged cases, including the spec's worked examples. Domain coverage target is ≥ 95%.

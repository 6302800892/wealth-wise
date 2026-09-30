---
name: drift-calculator
description: Fixed-point valuation and drift reference for WealthWise (AC-05, AC-06, BR-12 – BR-15, NFR-01). Load before touching drift_calculator.py, holdings_service.py, nav_service.py or any money arithmetic.
---

# Drift Calculator Skill

## Formulas
```
value_i    = units_i × NAV_i                        → quantize 0.01, ROUND_HALF_EVEN
total      = Σ value_i
current%_i = value_i × 100 / total                  → quantize 0.01, ROUND_HALF_EVEN   (skip when total = 0)
drift_i    = |current%_i − target%_i|               (target% from the latest recommendation's stored lines)
trigger    = max(drift) > threshold                 (strictly greater; threshold from WEALTHWISE_DRIFT_THRESHOLD_PCT)
```
An asset class that is held but not in the target has target 0.00. A class with zero units and no target is omitted.

## Status values
| Status | When | Drift fields |
|---|---|---|
| `OK` | total > 0 and a recommendation exists | populated |
| `NO_HOLDINGS` | total = 0 | `null` |
| `NO_RECOMMENDATION` | holdings exist but no recommendation | current% only |

## Worked example — portfolio E1 (use it in tests)
| Class | Units | NAV | Value | Current | Target | Drift |
|---|---|---|---|---|---|---|
| EQUITY | 4000.0000 | 150.0000 | 600,000.00 | 60.00 | 50.00 | 10.00 |
| DEBT | 10000.0000 | 25.0000 | 250,000.00 | 25.00 | 35.00 | 10.00 |
| GOLD | 2000.0000 | 50.0000 | 100,000.00 | 10.00 | 10.00 | 0.00 |
| CASH | 50000.0000 | 1.0000 | 50,000.00 | 5.00 | 5.00 | 0.00 |

Total 1,000,000.00 · max drift 10.00 → triggers at threshold 5.00, not at 12.00.

## Pitfalls (knowledge deposits)
- `float` anywhere in these layers fails `test_no_float.py` and the `no-float-money-check` hook.
- JSON numbers must never reach `Decimal`. `parse_fixed()` accepts **strings only**.
- Reading targets from the *active template* instead of the recommendation breaks the in-flight rule (AC-10.3).

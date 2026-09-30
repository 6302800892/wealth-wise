# WealthWise — Business Case

**Business case:** BC-AINE-008 · **Domain:** BFS / Wealth Management · **Status:** Implemented (capstone)

## 1. Problem
Retail investors at a mid-sized wealth management firm reach advice through a relationship manager. Profiling is done on paper or in spreadsheets. Allocation advice varies from advisor to advisor. Portfolios drift for months before anyone notices. The firm cannot serve smaller accounts profitably this way, and it cannot show a regulator why a customer received a particular recommendation.

The firm wants a **self-service robo-advisor** with four properties:
- It profiles customers consistently.
- It recommends an allocation using published, versioned rules, **not** machine learning.
- It tracks progress toward real life goals.
- It prompts customers to rebalance when their portfolio drifts.

Every decision must be reproducible and auditable.

## 2. Target users
| User | Need | What WealthWise gives them |
|---|---|---|
| **Retail investor** (customer) | Understand their risk appetite, know what to invest in, see progress toward goals, and be told when to act | A 6-question questionnaire, a clear risk band, an allocation per goal horizon, drift alerts and one-click rebalancing |
| **Advisor** | Oversee many customers and correct a profile when life changes | A customer list with drift alerts, a portfolio view, audited risk-band overrides and a manual-recommendation log |
| **Admin / product owner** | Change policy safely without breaking existing customers | Versioned rule sets and templates, immutable once published, with validation that blocks bad allocations |
| **Compliance / audit** (indirect) | Prove why advice was given | Append-only records of every assessment, assignment, override, recommendation and decision, with actor and timestamp |

## 3. Success metrics
| Metric | Target | How it is measured in this build |
|---|---|---|
| Recommendation reproducibility | 100% identical output for identical inputs | Input fingerprint plus idempotent POST (AC-04.4). The exhaustive scoring test covers all 15,625 answer sets. |
| Allocation integrity | 0 published templates not summing to 100.00 | DB invariant test, publish validation and the `allocation-sum-invariant-check` hook |
| Audit completeness | 100% of overrides and rebalancing decisions have actor + timestamp | Table CHECK and FK, `audit_log`, `test_override_requires_audit.py` |
| Time to profile and get a recommendation | < 5 minutes self-service | E2E customer journey (questionnaire → goal → recommendation) |
| Drift response | A proposal on the first NAV refresh after drift exceeds the threshold | Refresh cycle evaluates every eligible customer (AC-06.5) |
| Data protection | 0 PII or balance values in logs | Redacting JSON formatter, the `pii-log-check` hook, and a journey test with sentinel PII |

## 4. Domain rules (summary; `specs/app_spec.md` §8 is authoritative)
1. **Risk profiling.** Six questions, each option scored 1–5. Total 6–30: CONSERVATIVE 6–13, MODERATE 14–22, AGGRESSIVE 23–30.
2. **Goal horizon.** Under 36 months is SHORT, 36–84 is MEDIUM, and over 84 is LONG. Months are counted to the goal's target date.
3. **Allocation templates.** One row per band × horizon across EQUITY, DEBT, GOLD and CASH. Every row sums to exactly 100.00. Templates are versioned, and a published version can never change.
4. **Primary goal.** Highest priority wins, then the earliest target date. This goal sets the horizon of the portfolio recommendation.
5. **Drift.** drift = abs(current% − target%) per asset class. A rebalancing proposal is raised when any drift is **greater than** the threshold (default 5.00 percentage points).
6. **Rebalancing.** The proposal holds BUY/SELL quantities that restore the target. Units are truncated so nothing is overspent, and sells are capped at the units held. The customer accepts (stub orders only) or dismisses. Either way it is audited.
7. **Goal progress.** percent_complete = value of goal-tagged holdings / target amount. It is recorded on every daily NAV refresh.
8. **Advisor override.** It requires a reason from a fixed list plus a note. It is recorded with actor and time, and the next recommendation uses the new band.
9. **In-flight rule.** Customers keep the template version of their latest recommendation until they request a new one.
10. **Fixed point.** Money, units and percentages are never floating point.

## 5. Value proposition
- **For the firm:** the same advice quality at a fraction of the cost per account, so smaller accounts become viable. Policy changes become a versioned, validated release instead of a spreadsheet edit.
- **For customers:** transparent, consistent advice tied to their own goals, with prompts to act before drift compounds.
- **For compliance:** every recommendation can be reconstructed. The stored inputs (band, horizon, template version, goal) and the append-only history show exactly why it was made.
- **For engineering:** the platform was built entirely by Claude Code agents under supervision. Specs, guardrail hooks and architecture tests keep generated code inside the rules. The evidence is under `sprint-contracts/`, `specs/reviews/` and the MR history.

## 6. Scope boundaries
Out of scope, stubbed:
- A real brokerage. Orders are `STUB_SUBMITTED` only.
- Real-time market data. A daily synthetic NAV feed is used instead.
- FX. INR only.
- Tax optimisation.
- Real KYC. A boolean flag stands in.
- ML recommendations.
- Production deployment.

All data is synthetic.

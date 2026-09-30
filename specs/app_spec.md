# WealthWise — Application Specification (Root Spec)

| Field | Value |
|---|---|
| Spec ID | SPEC-APP-001 |
| Business case | BC-AINE-008 — Robo-Advisory & Portfolio Recommendation Platform |
| Domain | BFS — Wealth Management |
| Spec version | 1.0.0 |
| Status | Draft — awaiting human approval |
| Last updated | 2026-09-30 |

> **Spec-is-truth.** When this spec and the code disagree, the spec wins. Change the spec on purpose (bump the version, add a changelog entry), then regenerate the code. AC, NFR and BR identifiers are stable. Never renumber or reuse them.
>
> **No hand-coding.** Claude Code agents generate all production code, tests and migrations. Humans edit only specs, `CLAUDE.md` files, agent/skill/hook/command definitions and other substrate files.

---

## 1. How to use this spec

- This is the **root spec**. Per-feature specs (§17) add detail to it and must never contradict it.
- Harness pipeline entry point: `/spec specs/app_spec.md`. The planner breaks §9 down into epics and stories, then writes `specs/stories/` and `specs/features.json`.
- Every rule in §8 has a `BR-xx` ID. Every acceptance criterion has an `AC-NN` ID with Given-When-Then scenarios `AC-NN.n`. Every non-functional requirement has an `NFR-NN` ID. Tests, stories and sprint contracts reference these IDs.
- Terms in **MUST / MUST NOT / SHOULD** follow RFC 2119.

---

## 2. Product summary

**Problem.** A wealth management firm wants to offer retail investors a self-service robo-advisor. Today, profiling, allocation advice and rebalancing depend on advisors doing the work by hand. That makes advice slow, inconsistent and hard to audit.

**Solution.** WealthWise is a web platform with four parts:
1. A risk-profile questionnaire. It assigns a risk band with a deterministic score.
2. Rule-based portfolio recommendations. Each one comes from a versioned allocation template, chosen by risk band and goal horizon.
3. Goal tracking. Progress updates every time daily NAV is refreshed.
4. Drift detection. When drift passes a threshold, the customer gets a rebalancing proposal they can accept or dismiss.

Advisors can override a risk band. Every override is audited. Admins manage versioned rules and templates.

**Core constraint.** All recommendation logic is **deterministic and rule-based**. The system MUST NOT use machine learning, randomness or any external AI service at runtime.

---

## 3. Scope

### 3.1 In scope
- Risk-profile questionnaire, scoring and risk-band assignment (customer)
- Financial goals: create, list, view, update (customer)
- Portfolio recommendation by risk band and goal horizon (customer)
- Holdings, valuation and per-asset-class drift (customer)
- Rebalancing proposals with BUY/SELL quantities, plus accept/dismiss with audit (customer)
- Goal progress snapshots on each NAV refresh (system)
- Stub asset price feed: daily NAV per asset class on a configurable schedule (system)
- Advisor workbench: portfolio view, risk-band override, manual recommendation log (advisor)
- Admin: asset-class master, versioned risk rule sets, versioned allocation templates, manual NAV refresh (admin)

### 3.2 Out of scope
- Real exchange or brokerage integration. Orders are stubs and never executed.
- Real-time market data. Only the stubbed daily NAV exists.
- Multiple currencies or FX. The single currency is **INR**.
- Tax-loss harvesting and tax optimisation
- A real KYC document workflow. KYC is a boolean stub flag (§8.14).
- Machine-learning recommendations
- Production deployment, secret management, multi-region, email/SMS notifications

---

## 4. Users and roles

| Role | Who | Can do | MUST NOT do |
|---|---|---|---|
| `CUSTOMER` | Retail investor | Take the questionnaire. View own band. Manage own goals. View own recommendation, holdings and drift. Accept or dismiss own rebalancing proposals. | See any other customer's data. Call advisor or admin endpoints. |
| `ADVISOR` | Firm advisor | List customers. View any customer's portfolio. Override a risk band with a reason. Log manual recommendations. | Edit rules or templates. Accept or dismiss on a customer's behalf. |
| `ADMIN` | Platform admin | Manage asset classes. Draft and publish rule sets and templates. Trigger NAV refresh. | Call customer or advisor endpoints. Edit published versions. |

- Each user has exactly **one** role. Roles do not inherit from each other. An `ADMIN` is not an `ADVISOR`.
- A customer asking for another customer's resource gets `404 NOT_FOUND`, never `403`, so that resource IDs cannot be enumerated.

---

## 5. Technology stack (fixed)

Every choice below comes from the capstone's approved technology list. Anything not listed here or in §5.2 is **not permitted** without a spec change.

| Layer | Choice |
|---|---|
| Backend language | Python 3.12+ (3.13 used locally) |
| Backend framework | FastAPI (request/response schemas use Pydantic, which FastAPI bundles) |
| Database | SQLite through the Python standard-library `sqlite3` module. Tests use a temporary file DB. |
| Build and dependency management | Poetry (`pyproject.toml` + `poetry.lock`) |
| Backend tests | pytest, with coverage from pytest-cov (`coverage.xml`) |
| Architecture enforcement | import-linter, plus pytest architecture tests |
| Frontend | React (JavaScript/JSX), built with npm |
| Frontend unit tests | Vitest |
| UI / E2E validation | Playwright for Python (pytest-playwright) |
| MCP server | Playwright MCP (`.mcp.json`), used by the harness evaluator |
| CI | GitLab CI (`.gitlab-ci.yml`), with a Claude Code review job |
| Harness | Claude Harness Engine plugin (generator → evaluator → ratchet → PR) |
| Scripting agent | Claude Agent SDK for Python (`claude-agent-sdk`), used only under `scripts/` |

### 5.1 Standard library usage (no extra packages)
- `decimal.Decimal` for all fixed-point maths (NFR-01)
- `sqlite3` for persistence, `hashlib.pbkdf2_hmac` for password hashing, `secrets` for session tokens
- `logging` with a custom JSON formatter (NFR-06), and `contextvars` for correlation IDs
- `asyncio` for the NAV refresh schedule
- `uuid` for IDs, `datetime` for dates

### 5.2 Required supporting packages (only these)
| Package | Why it is unavoidable |
|---|---|
| `uvicorn` | ASGI server needed to run FastAPI |
| `httpx` (dev) | Needed by FastAPI's `TestClient` |
| `pytest-cov` (dev) | Coverage tool that produces the required coverage artefact |
| `pytest-playwright` (dev) | Playwright's official pytest integration |
| `vite`, `@vitejs/plugin-react` (dev, frontend) | React build tool. Vitest requires it. It is also the harness's default React preset. |

### 5.3 Explicitly not permitted
- ORMs (SQLAlchemy and others), migration frameworks (Alembic and others), and any database other than SQLite
- TypeScript, React Router or other routing libraries, UI component kits, CSS frameworks, state-management libraries, charting libraries
- Floating-point arithmetic on money, units, NAV or percentages (NFR-01)
- Docker, `uv`, `ruff`, `mypy`. In the harness `project-manifest.json`, set `linter` and `typechecker` to `"none"` so that the harness hooks `lint-on-save.js` and `typecheck.js` skip them.
- Any runtime call to an AI/LLM provider from `src/`

---

## 6. Architecture

### 6.1 Layers
Dependencies point **downward only**. A module may import only from layers below it.

| # | Layer | Package | Responsibility | May import |
|---|---|---|---|---|
| 1 | Types | `src/types/` | Enums, value objects (`Money`, `Percent`, `Units`, `Nav`), IDs, error classes | stdlib only |
| 2 | Domain | `src/domain/` | Pure deterministic business rules (§8). No I/O. | Types |
| 3 | Config | `src/config/` | Settings loaded from environment variables into a frozen dataclass, and the clock | Types, Domain |
| 4 | Repository | `src/repository/` | `sqlite3` access, the migration runner, one repository per aggregate | Types, Domain, Config |
| 5 | Service | `src/service/` | Use-case orchestration, transactions, audit writes | Types, Domain, Config, Repository |
| 6 | API (controllers) | `src/api/` | FastAPI routers, request/response schemas, auth dependencies, middleware, error handlers | Types, Config, Service |
| — | Composition root | `src/main.py` | App factory, lifespan, NAV scheduler wiring, static UI mount | everything |
| 7 | UI | `frontend/src/` | React pages and components. Talks to the backend only over HTTP. | its own modules |

### 6.2 Repository layout
```
/
├── CLAUDE.md                  # root context (+ per-module/per-folder CLAUDE.md files)
├── AGENTS.md                  # table of contents only
├── README.md                  # quick-start
├── plugin.json                # WealthWise substrate plugin manifest
├── .mcp.json                  # Playwright MCP
├── .gitlab-ci.yml
├── pyproject.toml / poetry.lock   # includes [tool.importlinter] and pytest config
├── src/
│   ├── types/  domain/  config/  repository/  service/  api/
│   └── main.py
├── migrations/                # 0001_<name>.sql … append-only (NFR-05)
├── seed/                      # nav_feed.csv, seed JSON (synthetic only)
├── tests/
│   ├── unit/domain/  unit/service/
│   ├── integration/api/
│   ├── architecture/
│   └── e2e/  (snapshots/)
├── frontend/
│   ├── package.json  vite.config.js  index.html
│   ├── src/  (config/ api/ hooks/ components/ pages/)
│   └── tests/unit/
├── scripts/                   # Claude Agent SDK scripts (engineering tooling only)
├── specs/                     # app_spec.md, <feature>_spec.md, stories/, reviews/, features.json
├── sprint-contracts/
├── docs/                      # business-case.md, architecture.md, tdd.md, knowledge-deposits.md,
│                              # fix-loops/, post-mortems/
└── .claude/                   # harness + project substrate
```

### 6.3 Enforced structural rules
Import-linter contracts go in `pyproject.toml`. A pytest test runs them, and CI runs them too.

| Contract | Rule |
|---|---|
| `layers` | `src.api` > `src.service` > `src.repository` > `src.config` > `src.domain` > `src.types` |
| `forbidden` | `sqlite3` may be imported **only** by `src.repository` |
| `forbidden` | `fastapi` and `starlette` may be imported **only** by `src.api` and `src.main` |
| `forbidden` | `src.api` MUST NOT import `src.repository`. Controllers go through services. |
| `forbidden` | `src.domain` and `src.types` MUST NOT import `logging`, `random`, `sqlite3`, `fastapi`, `datetime.now`-style clocks. Time is always passed in. |

Architecture tests in `tests/architecture/` (at least 6):
1. `test_layering.py`: import-linter contracts pass.
2. `test_no_float.py`: an AST scan of `src/domain`, `src/service` and `src/repository` finds no `float(` calls and no float literals (NFR-01).
3. `test_allocation_sum_invariant.py`: every row of every seeded or published template sums to exactly 100.00 (NFR-08).
4. `test_published_immutable.py`: `UPDATE`/`DELETE` on published rule-set or template rows is rejected at the DB level (NFR-08, AC-10).
5. `test_override_requires_audit.py`: an `ADVISOR_OVERRIDE` risk-band assignment cannot be persisted without a linked override audit record (NFR-08, AC-09).
6. `test_routes_have_auth.py`: every route except `/health` and `/api/v1/auth/login` declares a role dependency (NFR-04).
7. `test_append_only_tables.py`: every table listed in §12.2 rejects `UPDATE` and `DELETE` (NFR-02).
8. `test_ac_traceability.py`: every `AC-NN` in this spec has at least one test marked `@pytest.mark.ac("AC-NN")`.

### 6.4 Runtime
- One process. FastAPI serves `/api/v1/*`, `/health` and the built React app (`frontend/dist`) from **http://localhost:8000**.
- **Single start command:** `poetry run wealthwise`. It applies migrations, loads seed data if the DB is empty, builds the frontend if `frontend/dist` is missing (`npm --prefix frontend ci && npm --prefix frontend run build`), then starts uvicorn.
- Dev mode: `npm --prefix frontend run dev` (Vite on 5173, proxying `/api` to 8000).

---

## 7. Domain model

### 7.1 Glossary
| Term | Meaning |
|---|---|
| Risk band | `CONSERVATIVE`, `MODERATE` or `AGGRESSIVE` |
| Rule set | A versioned questionnaire: questions, option scores and band thresholds |
| Template set | A versioned group of allocation templates, one row set per (risk band × horizon bucket) |
| Horizon bucket | `SHORT`, `MEDIUM` or `LONG`, derived from months until a goal's target date |
| Primary goal | The goal that drives the portfolio recommendation (BR-10) |
| Portfolio recommendation | Target allocation for a customer. It is immutable and records the versions it used. |
| Drift | `abs(current% − target%)` per asset class, in percentage points |
| Rebalancing recommendation | A proposal with BUY/SELL/HOLD lines, created when drift exceeds the threshold |
| NAV | Net asset value per unit of an asset class for a given date |

### 7.2 Enums
- `RiskBand`: `CONSERVATIVE`, `MODERATE`, `AGGRESSIVE`
- `HorizonBucket`: `SHORT`, `MEDIUM`, `LONG`
- `Role`: `CUSTOMER`, `ADVISOR`, `ADMIN`
- `GoalType`: `RETIREMENT`, `EDUCATION`, `HOME`, `OTHER`
- `GoalPriority`: `HIGH`, `MEDIUM`, `LOW`
- `BandSource`: `QUESTIONNAIRE`, `ADVISOR_OVERRIDE`
- `OverrideReason`: `CHANGE_IN_CIRCUMSTANCES`, `QUESTIONNAIRE_MISUNDERSTOOD`, `ADVISOR_ASSESSMENT`, `CUSTOMER_REQUEST`
- `VersionStatus`: `DRAFT`, `PUBLISHED`
- `TradeAction`: `BUY`, `SELL`, `HOLD`
- `RebalancingStatus` (derived from latest decision): `OPEN`, `ACCEPTED`, `DISMISSED`, `SUPERSEDED`
- `StubOrderStatus`: `STUB_SUBMITTED`

### 7.3 Fixed-point representation (NFR-01)
| Quantity | Python type | Scale | Stored in SQLite as | JSON wire format |
|---|---|---|---|---|
| Money (INR) | `Decimal` | 2 dp | `INTEGER` paise (×100) | string `"600000.00"` |
| Percentage | `Decimal` | 2 dp | `INTEGER` basis points (×100, so 100% = 10000) | string `"50.00"` |
| Units | `Decimal` | 4 dp | `INTEGER` (×10 000) | string `"666.6666"` |
| NAV | `Decimal` | 4 dp | `INTEGER` (×10 000) | string `"150.0000"` |
| Score | `int` | — | `INTEGER` | number |

- Requests MUST send money, units, NAV and percentages as **JSON strings**. A JSON number in these fields is rejected with `422 VALIDATION_FAILED`.
- The frontend only displays these strings. It MUST NOT do arithmetic on them.

### 7.4 Entities
| Entity | Key fields | Mutability |
|---|---|---|
| `users` | id, username, password_hash, role, customer_id? | mutable |
| `sessions` | token_hash, user_id, expires_at | mutable |
| `customers` | id, full_name 🔒, email 🔒, date_of_birth 🔒, kyc_verified | mutable |
| `asset_classes` | code, name, display_order, is_active | mutable (master data) |
| `risk_rule_set_versions` | version, status, definition_json, created_by, published_by, published_at | immutable once `PUBLISHED` |
| `allocation_template_set_versions` | version, status, created_by, published_by, published_at | immutable once `PUBLISHED` |
| `allocation_template_rows` | template_version, risk_band, horizon_bucket, asset_class_code, target_bp | immutable once parent `PUBLISHED` |
| `risk_assessments` | id, customer_id, rule_set_version, answers_json, total_score, computed_band, created_at | **append-only** |
| `risk_band_assignments` | id, customer_id, risk_band, source, assessment_id?, override_id?, rule_set_version, assigned_by, assigned_at | **append-only** |
| `risk_band_overrides` | id, customer_id, previous_band, new_band, reason_code, note 🔒, actor_user_id, created_at | **append-only** |
| `goals` | id, customer_id, name, goal_type, target_amount, target_date, priority, created_at, updated_at, archived_at? | mutable (soft delete) |
| `portfolio_recommendations` | id, customer_id, goal_id, risk_band_assignment_id, risk_band, horizon_bucket, template_version, as_of_date, input_fingerprint, created_at | **append-only** |
| `portfolio_recommendation_lines` | recommendation_id, asset_class_code, target_bp | **append-only** |
| `holdings` | id, customer_id, goal_id?, asset_class_code, units, updated_at | mutable |
| `nav_prices` | nav_date, asset_class_code, nav | **append-only**, unique(nav_date, asset_class_code) |
| `goal_progress_snapshots` | id, goal_id, nav_date, current_value, target_amount, percent_complete | **append-only**, unique(goal_id, nav_date) |
| `rebalancing_recommendations` | id, customer_id, portfolio_recommendation_id, template_version, nav_date, threshold_bp, total_value, max_drift_bp, created_at | **append-only** |
| `rebalancing_lines` | rebalancing_id, asset_class_code, current_bp, target_bp, drift_bp, action, units, trade_value | **append-only** |
| `rebalancing_decisions` | id, rebalancing_id, status, reason?, actor_user_id?, decided_at | **append-only** |
| `stub_orders` | id, rebalancing_id, asset_class_code, action, units, status, created_at | **append-only** |
| `manual_recommendations` | id, customer_id, advisor_user_id, note 🔒, created_at | **append-only** |
| `audit_log` | id, actor_user_id, action, entity_type, entity_id, correlation_id, details_json (no PII), created_at | **append-only** |
| `schema_migrations` | filename, checksum_sha256, applied_at | append-only |

🔒 = PII or sensitive text. It MUST never be logged (NFR-03).

---

## 8. Business rules (deterministic)

Every rule is a pure function in `src/domain/`. Rules receive the date, versions and thresholds as arguments. They never read the clock, the DB or the environment.

| Rule file (`src/domain/`) | Rules |
|---|---|
| `risk_band_scorer.py` | BR-01 – BR-04 |
| `horizon_resolver.py` | BR-08 |
| `allocation_template_validator.py` | BR-09, BR-22 |
| `recommendation_resolver.py` | BR-10 – BR-11 |
| `drift_calculator.py` | BR-12 – BR-14 |
| `rebalancing_proposer.py` | BR-15 – BR-17 |
| `goal_progress_calculator.py` | BR-19 |
| `override_policy.py` | BR-20 |
| `version_policy.py` | BR-21 – BR-23 |

### 8.1 Risk questionnaire — rule set v1 (seed)
**BR-01.** A rule set MUST contain at least 6 questions. Each question has 5 options scored 1–5.

| # | Question | Options (score) |
|---|---|---|
| Q1 | What is your age? | 60+ (1) · 50–59 (2) · 40–49 (3) · 30–39 (4) · under 30 (5) |
| Q2 | When will you need most of this money? | < 1 yr (1) · 1–3 yrs (2) · 3–5 yrs (3) · 5–10 yrs (4) · > 10 yrs (5) |
| Q3 | How stable is your income? | Very unstable (1) · Unstable (2) · Moderately stable (3) · Stable (4) · Very stable, several sources (5) |
| Q4 | Your portfolio falls 20% in a month. You… | Sell everything (1) · Sell some (2) · Do nothing (3) · Buy a little more (4) · Buy a lot more (5) |
| Q5 | Your investing experience? | None (1) · Savings/FDs only (2) · Mutual funds (3) · Stocks and mutual funds (4) · Advanced products (5) |
| Q6 | Your main objective? | Protect capital (1) · Regular income (2) · Balanced (3) · Growth (4) · Maximum growth (5) |

**BR-02.** `total_score` is the sum of the chosen option scores. Range for v1: 6–30.

**BR-03.** Band thresholds for v1. They are inclusive, contiguous and non-overlapping.

| Band | Score range |
|---|---|
| CONSERVATIVE | 6 – 13 |
| MODERATE | 14 – 22 |
| AGGRESSIVE | 23 – 30 |

**BR-04.** A submission MUST contain exactly one answer for every question in the named rule-set version, and every option ID MUST belong to its question. Anything else is rejected and nothing is saved.

### 8.2 Effective risk band
**BR-05.** A customer's effective band is the `risk_band` of their **latest** `risk_band_assignments` row, whatever its source.

**BR-06.** A questionnaire submission creates one `risk_assessments` row and one assignment with `source = QUESTIONNAIRE`.

**BR-07.** An assignment with `source = ADVISOR_OVERRIDE` MUST reference a `risk_band_overrides` row (enforced by a DB `CHECK` constraint plus a service rule).

### 8.3 Goal horizon
**BR-08.**
`months = (target.year − as_of.year) × 12 + (target.month − as_of.month) − (1 if target.day < as_of.day else 0)`

| Bucket | Months |
|---|---|
| SHORT | months < 36 (includes past-due goals, where months ≤ 0) |
| MEDIUM | 36 ≤ months ≤ 84 |
| LONG | months > 84 |

### 8.4 Allocation templates — template set v1 (seed)
**BR-09.** Every (band, horizon) row MUST list every asset class in the template set. Each percentage MUST be 0.00–100.00, and the row MUST sum to **exactly 100.00**.

| Band | Horizon | EQUITY | DEBT | GOLD | CASH | Sum |
|---|---|---|---|---|---|---|
| CONSERVATIVE | SHORT | 10 | 60 | 10 | 20 | 100 |
| CONSERVATIVE | MEDIUM | 20 | 60 | 10 | 10 | 100 |
| CONSERVATIVE | LONG | 30 | 55 | 10 | 5 | 100 |
| MODERATE | SHORT | 30 | 50 | 10 | 10 | 100 |
| MODERATE | MEDIUM | 50 | 35 | 10 | 5 | 100 |
| MODERATE | LONG | 60 | 27 | 10 | 3 | 100 |
| AGGRESSIVE | SHORT | 45 | 40 | 10 | 5 | 100 |
| AGGRESSIVE | MEDIUM | 70 | 20 | 7 | 3 | 100 |
| AGGRESSIVE | LONG | 80 | 12 | 5 | 3 | 100 |

### 8.5 Recommendation resolution
**BR-10. Primary goal.** Among the customer's non-archived goals, pick the one with the highest priority (`HIGH` > `MEDIUM` > `LOW`). Break ties by earliest `target_date`, then earliest `created_at`, then lowest `id`. A request can name a specific `goal_id` instead.

**BR-11.** The allocation is the template row (effective band, horizon of the goal, **active** template version), where `as_of` is the injected business date. The `input_fingerprint` is SHA-256 of canonical JSON `{risk_band, horizon_bucket, template_version, goal_id}`.
- If the customer's latest recommendation has the same fingerprint, the existing recommendation is returned (`200`) and no new row is created.
- Otherwise a new recommendation is created (`201`).
- The same inputs therefore always produce identical output.

### 8.6 Valuation and drift
**BR-12.** `value = units × NAV` for the latest `nav_date`, quantised to 0.01 (`ROUND_HALF_EVEN`). `total = Σ value`.

**BR-13.** `current% = value × 100 / total`, quantised to 0.01 (`ROUND_HALF_EVEN`). If `total = 0`, drift is not computed and the status is `NO_HOLDINGS`.

**BR-14.** `drift = abs(current% − target%)` in percentage points, where `target%` comes from the customer's **latest portfolio recommendation**, using the template version recorded on it. An asset class that is held but missing from the target has `target% = 0.00`.

### 8.7 Rebalancing
**BR-15. Trigger.** A rebalancing recommendation is generated when `max(drift) > threshold`. The comparison is **strictly greater than**. The threshold comes from config `WEALTHWISE_DRIFT_THRESHOLD_PCT` (default `5.00`) and is recorded on each recommendation.

**BR-16. Quantities.** For each asset class:
- `target_value = total × target% / 100`, quantised to 0.01 (`HALF_EVEN`)
- `delta = target_value − value`
- `units = abs(delta) / NAV`, quantised to 0.0001 (`ROUND_DOWN`)
- Action is `BUY` if `delta > 0` and `units > 0`, `SELL` if `delta < 0` and `units > 0`, otherwise `HOLD`.
- `SELL` units are capped at the units currently held.
- `CASH` always has NAV `1.0000`.

**BR-17. Evaluation lifecycle.** Evaluation runs after every NAV refresh, for each KYC-verified customer who has holdings and a portfolio recommendation. It also runs on demand. Each evaluation first marks any `OPEN` rebalancing recommendation for that customer as `SUPERSEDED`, then creates a new one only if BR-15 triggers.

**BR-18. Decisions.** Only an `OPEN` recommendation can be accepted or dismissed, and only by its own customer.
- Accepting creates one `stub_orders` row per BUY/SELL line with status `STUB_SUBMITTED`. Holdings do **not** change, because execution is out of scope.
- Every decision writes a `rebalancing_decisions` row and an `audit_log` row, both with actor and timestamp.

### 8.8 Goal progress
**BR-19.** `current_goal_value = Σ value` of the holdings tagged with that `goal_id`. `percent_complete = current_goal_value × 100 / target_amount`, quantised to 0.01 (`HALF_EVEN`).
- The value is not capped. At 100.00 or above, the goal status is `ACHIEVED`.
- Each NAV refresh writes one snapshot per non-archived goal for that `nav_date`. Running it again for the same date is a no-op.

### 8.9 Advisor override
**BR-20.** An override needs all of the following:
- a `new_band` different from the current effective band
- a `reason_code` from `OverrideReason`
- a `note` of 1–1000 characters after trimming

It atomically writes a `risk_band_overrides` row (previous band, new band, reason, note, actor, timestamp), an `ADVISOR_OVERRIDE` assignment that references it, and an `audit_log` row.

### 8.10 Versioning and immutability
**BR-21.** Rule sets and template sets each have integer versions: 1, 2, 3 and so on.
- At most one `DRAFT` of each type can exist at a time. It is created by cloning the active version.
- The **active** version is the highest `PUBLISHED` version.

**BR-22. Publish validation.**
- Templates: BR-09 holds for all 9 (band × horizon) rows, and every active asset class is present.
- Rule sets: BR-01 holds, and the band thresholds are contiguous, non-overlapping and cover the full score range [min, max].

**BR-23.** A `PUBLISHED` version and its child rows are **immutable**. The API returns `409 VERSION_IMMUTABLE`, and SQLite triggers `RAISE(ABORT)` on any `UPDATE` or `DELETE`.
- Existing assessments and recommendations keep the version they recorded. Drift and rebalancing always use the template version on the customer's latest recommendation (the in-flight rule).
- A questionnaire submitted against a version that is no longer active returns `409 RULE_SET_NOT_ACTIVE`.

### 8.11 KYC stub, NAV feed stub
**BR-24.** `customers.kyc_verified` is a stub flag. If it is `false`, recommendation and rebalancing endpoints return `403 KYC_NOT_VERIFIED`. The questionnaire and goals remain available.

**BR-25.** The NAV feed stub reads `seed/nav_feed.csv` (`nav_date, asset_class_code, nav`).
- Each refresh ingests the next `nav_date` that has not been processed yet.
- When the file runs out, it carries the last NAVs forward to the next calendar day.
- Schedule: `WEALTHWISE_NAV_REFRESH_INTERVAL_SECONDS` (default `0`, meaning disabled; trigger it manually).
- One refresh runs these steps in order: ingest NAV → goal snapshots (BR-19) → rebalancing evaluation (BR-17).

---

## 9. Functional acceptance criteria

Every AC below MUST have at least one test tagged with its ID (§15.2). The worked-example data used in several ACs:

> **Example portfolio E1.** Target: MODERATE / MEDIUM (template v1) = EQUITY 50 · DEBT 35 · GOLD 10 · CASH 5. NAV: EQUITY 150.0000 · DEBT 25.0000 · GOLD 50.0000 · CASH 1.0000. Holdings: EQUITY 4000.0000 u (600,000.00) · DEBT 10000.0000 u (250,000.00) · GOLD 2000.0000 u (100,000.00) · CASH 50000.0000 u (50,000.00). Total 1,000,000.00.

### AC-01 — Risk-profile questionnaire assigns a deterministic risk band
- **AC-01.1** Given rule set v1 is active, when a customer requests the questionnaire, then the response contains `rule_set_version = 1` and 6 questions, each with 5 options.
- **AC-01.2** Given a customer answers all 6 questions with options scoring 3,3,3,3,2,2, when they submit, then `total_score = 16`, `risk_band = MODERATE`, the response is `201`, and one assessment plus one `QUESTIONNAIRE` assignment are saved.
- **AC-01.3** Given scores totalling 6, 13, 14, 22, 23 and 30, when scored, then the bands are CONSERVATIVE, CONSERVATIVE, MODERATE, MODERATE, AGGRESSIVE and AGGRESSIVE.
- **AC-01.4** Given a submission with a missing question, a duplicate answer, or an option that belongs to another question, when submitted, then the response is `422 INVALID_ANSWERS` and nothing is saved.
- **AC-01.5** Given every one of the 5⁶ = 15,625 answer combinations, when scored twice, then each maps to exactly one band and both runs give identical results.
- **AC-01.6** Given a customer has submitted the questionnaire, when they view their risk profile, then they see `risk_band`, `source = QUESTIONNAIRE`, `rule_set_version` and `assigned_at`.

### AC-02 — Versioned allocation templates that always sum to 100
- **AC-02.1** Given template set v1, when it is loaded, then it contains 9 (band × horizon) rows covering EQUITY, DEBT, GOLD and CASH, and every row sums to exactly `100.00`.
- **AC-02.2** Given a draft template whose row sums to 99.00 or 100.01, when an admin publishes it, then the response is `422 ALLOCATION_SUM_INVALID` naming the failing row, and the version stays `DRAFT`.
- **AC-02.3** Given a draft with a negative percentage or one above 100.00, when saved, then the response is `422 VALIDATION_FAILED`.
- **AC-02.4** Given a recommendation is returned, when its lines are summed, then the total is exactly `"100.00"` and the response includes `template_version`.

### AC-03 — Customers create multiple financial goals
- **AC-03.1** Given a customer, when they create a goal with `name`, `goal_type = HOME`, `target_amount = "2000000.00"`, `target_date = 2031-06-30` and `priority = HIGH`, then the response is `201` with the goal ID and the same values echoed back.
- **AC-03.2** Given a customer who already has one goal, when they create a second and a third, then listing returns all three, ordered by priority, then target_date.
- **AC-03.3** Given `target_amount` ≤ 0, above `1000000000.00`, with more than 2 dp, or sent as a JSON number, when submitted, then the response is `422`.
- **AC-03.4** Given a `target_date` on or before today, or a priority outside the enum, when submitted, then the response is `422`.
- **AC-03.5** Given customer A's goal ID, when customer B requests it, then the response is `404`.

### AC-04 — Deterministic recommendation by risk band and goal horizon
- **AC-04.1** Given band MODERATE and a primary goal 120 months away (horizon LONG), when a recommendation is requested, then the allocation is EQUITY 60.00 · DEBT 27.00 · GOLD 10.00 · CASH 3.00, and it records `template_version`, `horizon_bucket` and `risk_band`.
- **AC-04.2** Given as_of = 2026-09-30 and target dates 2029-09-29, 2029-09-30, 2033-09-30 and 2033-10-30, when the horizon is resolved, then the buckets are SHORT, MEDIUM, MEDIUM and LONG.
- **AC-04.3** Given a HIGH goal due in 2040 and a MEDIUM goal due in 2028, when no `goal_id` is supplied, then the HIGH goal is primary (BR-10).
- **AC-04.4** Given identical inputs, when a recommendation is requested twice, then the second call returns `200` with the same recommendation ID, lines and fingerprint, and no new row is created.
- **AC-04.5** Given a customer with no risk band, no goals, or `kyc_verified = false`, when a recommendation is requested, then the response is `409 RISK_PROFILE_REQUIRED`, `409 GOAL_REQUIRED` or `403 KYC_NOT_VERIFIED` respectively.

### AC-05 — Holdings valuation and per-asset-class drift
- **AC-05.1** Given portfolio E1, when holdings are viewed, then values are 600,000.00 / 250,000.00 / 100,000.00 / 50,000.00 and the total is 1,000,000.00.
- **AC-05.2** Given portfolio E1, when drift is calculated, then current% is 60.00 / 25.00 / 10.00 / 5.00 and drift is 10.00 / 10.00 / 0.00 / 0.00.
- **AC-05.3** Given holdings whose current% rounds (for example 1/3 of the total), when calculated, then results are quantised to 0.01 with `ROUND_HALF_EVEN` using `Decimal` only.
- **AC-05.4** Given a customer with no holdings, when holdings are viewed, then total is `"0.00"`, drift is `null` and `drift_status = NO_HOLDINGS`.

### AC-06 — Rebalancing triggered when drift exceeds the threshold
- **AC-06.1** Given portfolio E1 and threshold 5.00, when rebalancing is evaluated, then an `OPEN` rebalancing recommendation is created with `max_drift = 10.00`.
- **AC-06.2** Given a portfolio whose largest drift is exactly 5.00, when evaluated, then nothing is created. Given 5.01, one is created.
- **AC-06.3** Given portfolio E1 and threshold 12.00, when evaluated, then nothing is created.
- **AC-06.4** Given an existing `OPEN` recommendation, when evaluation runs again, then the old one becomes `SUPERSEDED` and at most one `OPEN` recommendation exists.
- **AC-06.5** Given a NAV refresh, when it completes, then evaluation has run for every eligible customer (BR-17).

### AC-07 — BUY/SELL proposal with accept or dismiss and audit
- **AC-07.1** Given portfolio E1, when the proposal is generated, then it has a UUID `recommendation_id` and lines EQUITY `SELL 666.6666` · DEBT `BUY 4000.0000` · GOLD `HOLD 0.0000` · CASH `HOLD 0.0000`.
- **AC-07.2** Given a computed SELL larger than the units held, when proposed, then SELL units equal the units held.
- **AC-07.3** Given an `OPEN` recommendation, when the customer accepts it, then its status is `ACCEPTED`, 2 stub orders exist with `STUB_SUBMITTED`, holdings are unchanged, and the decision and audit rows record actor and timestamp.
- **AC-07.4** Given an `OPEN` recommendation, when the customer dismisses it with an optional reason (≤ 500 chars), then its status is `DISMISSED` with actor and timestamp audited.
- **AC-07.5** Given an `ACCEPTED`, `DISMISSED` or `SUPERSEDED` recommendation, when accept or dismiss is attempted, then the response is `409 RECOMMENDATION_NOT_OPEN`. Given another customer's recommendation, the response is `404`.

### AC-08 — Goal progress updated on each daily NAV refresh
- **AC-08.1** Given a goal with target 2,000,000.00 and tagged holdings EQUITY 2000 u @150.0000 plus DEBT 8000 u @25.0000, when progress is computed, then `current_goal_value = 500000.00` and `percent_complete = 25.00`.
- **AC-08.2** Given that goal, when a NAV refresh sets EQUITY to 153.0000, then a new snapshot for that `nav_date` shows 506,000.00 and 25.30.
- **AC-08.3** Given the refresh for the same `nav_date` runs twice, then exactly one snapshot per goal exists for that date.
- **AC-08.4** Given a goal with no tagged holdings, then `percent_complete = 0.00`. Given a value at or above the target, then the status is `ACHIEVED` and the percentage is not capped.

### AC-09 — Advisor risk-band override with an audit trail
- **AC-09.1** Given a customer whose band is MODERATE, when an advisor overrides it to CONSERVATIVE with `reason_code = CHANGE_IN_CIRCUMSTANCES` and a note, then the response is `201`, the effective band is CONSERVATIVE with `source = ADVISOR_OVERRIDE`, and the override stores previous band, new band, reason, note, `actor_user_id` and `created_at`.
- **AC-09.2** Given a missing reason, a blank or whitespace-only note, or a note over 1000 characters, then the response is `422`. Given `new_band` equal to the current band, the response is `422 BAND_UNCHANGED`.
- **AC-09.3** Given a `CUSTOMER` or `ADMIN` token, when calling the override endpoint, then the response is `403`.
- **AC-09.4** Given an override, when the customer next requests a recommendation, then it uses the overridden band.
- **AC-09.5** Given several overrides, when an advisor views the audit history, then all appear newest first, and the customer view shows the band source but **not** the advisor's note.

### AC-10 — Versioned rules and templates, immutable once published, with the in-flight rule
- **AC-10.1** Given a template draft v2, when an admin publishes it, then v2 is `PUBLISHED`, active, and records `published_by` and `published_at`.
- **AC-10.2** Given published v1, when an admin tries to edit it through the API, then the response is `409 VERSION_IMMUTABLE`. When a raw SQL `UPDATE` or `DELETE` targets it, then SQLite aborts.
- **AC-10.3** Given a customer with a recommendation on template v1, when v2 (with different MODERATE/MEDIUM percentages) is published, then that customer's drift and rebalancing still use v1 targets until they request a new recommendation, which uses v2.
- **AC-10.4** Given rule set v2 was published after a customer loaded v1, when they submit v1 answers, then the response is `409 RULE_SET_NOT_ACTIVE`.
- **AC-10.5** Given a rule-set draft with overlapping or gapped band thresholds, when published, then the response is `422` and it stays `DRAFT`.

---

## 10. Non-functional requirements

| ID | Requirement | How it is enforced and verified |
|---|---|---|
| NFR-01 | Portfolio values, percentages and drift use fixed point, never floating point | `Decimal` + integer storage (§7.3); JSON numbers rejected; `test_no_float.py`; unit tests with rounding edge cases |
| NFR-02 | Risk-band assignments, recommendations, rebalancing actions and overrides are append-only | SQLite `BEFORE UPDATE/DELETE … RAISE(ABORT)` triggers on every §12.2 table; repositories expose no update/delete; `test_append_only_tables.py` |
| NFR-03 | PII and financial-position data never reach logs | Logs carry only IDs, codes, counts and durations. A redaction filter drops denylisted keys (`full_name`, `email`, `date_of_birth`, `note`, `units`, `value`, `amount`, `target_amount`, `total`, `password`, `token`). A test runs all journeys with sentinel PII and asserts none of it appears in captured logs. |
| NFR-04 | Auth boundary at the controller layer, with customer/advisor/admin separated | FastAPI dependency `require_role(Role.X)` on every router; bearer session tokens (PBKDF2 passwords, SHA-256-hashed tokens, TTL from `WEALTHWISE_SESSION_TTL_MINUTES`); `test_routes_have_auth.py`; role-matrix integration tests (401/403/404) |
| NFR-05 | Database, policy and template migrations are append-only | Numbered `migrations/NNNN_*.sql`. The runner records a SHA-256 per file and **refuses to start** if an applied file's checksum changes. Policy/template changes ship as new versions or new migrations only. CI checks that no existing migration file was changed in the MR diff. |
| NFR-06 | Structured JSON logs with request correlation IDs | Every log line is JSON with `ts`, `level`, `logger`, `event`, `correlation_id`. Middleware reads or creates `X-Correlation-ID` and echoes it in the response and in error bodies. Tested. |
| NFR-07 | Health endpoint returns 200 within 1 s of a successful startup | `GET /health` → `{"status":"ok","db":"ok"}` using a cheap `SELECT 1`. A test asserts status 200 and latency < 1 s after the app starts. |
| NFR-08 | Architecture rules enforced as tests | `tests/architecture/` (§6.3): allocation sum = 100, published immutability, override needs an audit record, layering |

### 10.1 Error envelope
Every error uses this shape:
```json
{ "error": { "code": "ALLOCATION_SUM_INVALID", "message": "Row MODERATE/MEDIUM sums to 99.00", "details": {}, "correlation_id": "…" } }
```
Codes: `VALIDATION_FAILED`, `INVALID_ANSWERS`, `UNAUTHENTICATED` (401), `FORBIDDEN` (403), `KYC_NOT_VERIFIED` (403), `NOT_FOUND` (404), `RULE_SET_NOT_ACTIVE`, `VERSION_IMMUTABLE`, `DRAFT_ALREADY_EXISTS`, `RISK_PROFILE_REQUIRED`, `GOAL_REQUIRED`, `RECOMMENDATION_REQUIRED`, `RECOMMENDATION_NOT_OPEN` (all 409), `ALLOCATION_SUM_INVALID`, `BAND_UNCHANGED` (both 422).

---

## 11. API contract (prefix `/api/v1` unless noted)

| Method | Path | Role | Purpose | AC |
|---|---|---|---|---|
| GET | `/health` (no prefix) | public | Liveness + DB check | NFR-07 |
| POST | `/auth/login` | public | Username + password → bearer token | NFR-04 |
| POST | `/auth/logout` | any | Revoke token | NFR-04 |
| GET | `/auth/me` | any | Current user and role | NFR-04 |
| GET | `/questionnaire` | CUSTOMER | Active rule set questions | AC-01 |
| POST | `/me/risk-assessments` | CUSTOMER | Submit answers → band | AC-01, AC-10 |
| GET | `/me/risk-profile` | CUSTOMER | Effective band and source | AC-01, AC-09 |
| POST / GET | `/me/goals` | CUSTOMER | Create / list goals | AC-03 |
| GET / PATCH | `/me/goals/{goal_id}` | CUSTOMER | View / update a goal (archive with `archived: true`) | AC-03 |
| GET | `/me/goals/{goal_id}/progress` | CUSTOMER | Latest snapshot and history | AC-08 |
| POST | `/me/recommendations` | CUSTOMER | Generate or return the recommendation (optional `goal_id`) | AC-02, AC-04 |
| GET | `/me/recommendations/latest` | CUSTOMER | Latest recommendation | AC-02, AC-04 |
| GET | `/me/holdings` | CUSTOMER | Holdings, values, current%, drift | AC-05 |
| POST | `/me/holdings` | CUSTOMER | Record or update a simulated holding `{asset_class_code, goal_id?, units}` | AC-05 |
| POST | `/me/rebalancing/evaluate` | CUSTOMER | On-demand drift evaluation | AC-06 |
| GET | `/me/rebalancing` | CUSTOMER | List proposals with status | AC-06, AC-07 |
| POST | `/me/rebalancing/{id}/accept` | CUSTOMER | Accept → stub orders | AC-07 |
| POST | `/me/rebalancing/{id}/dismiss` | CUSTOMER | Dismiss with optional reason | AC-07 |
| GET | `/advisor/customers` | ADVISOR | Customer list (ID, name, band, KYC, open alerts) | — |
| GET | `/advisor/customers/{id}/portfolio` | ADVISOR | Band, goals, holdings, drift, rebalancing | AC-05, AC-09 |
| POST | `/advisor/customers/{id}/risk-band-overrides` | ADVISOR | Override band | AC-09 |
| GET | `/advisor/customers/{id}/audit` | ADVISOR | Override and decision history | AC-07, AC-09 |
| POST | `/advisor/customers/{id}/manual-recommendations` | ADVISOR | Log a manual recommendation note | — |
| GET / POST / PATCH | `/admin/asset-classes[/{code}]` | ADMIN | Asset-class master | AC-02 |
| GET / POST | `/admin/risk-rule-sets` | ADMIN | List versions / create draft | AC-10 |
| PUT | `/admin/risk-rule-sets/{version}` | ADMIN | Edit draft (409 if published) | AC-10 |
| POST | `/admin/risk-rule-sets/{version}/publish` | ADMIN | Validate and publish | AC-10 |
| GET / POST | `/admin/allocation-templates` | ADMIN | List versions / create draft | AC-02, AC-10 |
| PUT | `/admin/allocation-templates/{version}` | ADMIN | Edit draft (409 if published) | AC-02, AC-10 |
| POST | `/admin/allocation-templates/{version}/publish` | ADMIN | Validate and publish | AC-02, AC-10 |
| POST | `/admin/nav/refresh` | ADMIN | Run one NAV refresh cycle (BR-25) | AC-06, AC-08 |
| GET | `/admin/nav/latest` | ADMIN | Latest NAV per asset class | AC-05 |

Lists use cursor pagination: `{ "items": [], "next_cursor": null, "total": 0 }`.

---

## 12. Persistence and migrations

### 12.1 Rules
- The schema lives only in `migrations/NNNN_description.sql`, applied in order by `src/repository/migrations.py`.
- Applied files are **never edited or deleted** (NFR-05). Fixes go in a new file.
- Seed data for asset classes, rule set v1 and template set v1 ships as migrations (policy migrations). Demo customers and holdings load from `seed/` when the DB is empty.
- IDs are UUID4 text. Every table has `created_at`. Mutable tables also have `updated_at`.
- `PRAGMA foreign_keys = ON`. Foreign keys are declared explicitly.

### 12.2 Append-only tables (DB triggers + no repository update/delete)
`risk_assessments`, `risk_band_assignments`, `risk_band_overrides`, `portfolio_recommendations`, `portfolio_recommendation_lines`, `nav_prices`, `goal_progress_snapshots`, `rebalancing_recommendations`, `rebalancing_lines`, `rebalancing_decisions`, `stub_orders`, `manual_recommendations`, `audit_log`, `schema_migrations`.

Published rows of `risk_rule_set_versions`, `allocation_template_set_versions` and `allocation_template_rows` are protected by conditional triggers (BR-23).

---

## 13. User interface

React (JSX), plain CSS, hash-based routing written in-app. Every interactive element has a `data-testid`.

| Role | Route | Screen | AC |
|---|---|---|---|
| all | `#/login` | Login with demo users | NFR-04 |
| CUSTOMER | `#/dashboard` | Band badge, goal progress bars, open rebalancing alert | AC-01, AC-06, AC-08 |
| CUSTOMER | `#/risk-profile` | Questionnaire (6 questions), result card | AC-01 |
| CUSTOMER | `#/goals` | Goal list and create/edit form | AC-03, AC-08 |
| CUSTOMER | `#/recommendation` | Allocation table plus CSS bar, with template version and horizon | AC-02, AC-04 |
| CUSTOMER | `#/holdings` | Holdings table: value, current%, target%, drift (highlighted when above threshold) | AC-05 |
| CUSTOMER | `#/rebalancing` | Open proposal with BUY/SELL lines, Accept / Dismiss, history | AC-06, AC-07 |
| ADVISOR | `#/advisor/customers` | Customer list | — |
| ADVISOR | `#/advisor/customers/:id` | Portfolio view, override form, manual recommendation form, audit list | AC-09 |
| ADMIN | `#/admin/asset-classes` | Asset-class master | AC-02 |
| ADMIN | `#/admin/rule-sets` | Versions, draft editor, publish | AC-10 |
| ADMIN | `#/admin/templates` | Versions, 3×3 editor with live row sums, publish | AC-02, AC-10 |
| ADMIN | `#/admin/nav` | Latest NAV, "Run refresh" button | AC-08 |

**Responsive layout (required).** Every screen MUST work at 375 × 812 and 1280 × 800.
- Below 640 px, the side nav collapses into a top menu toggle and data tables become stacked cards.
- E2E tests run both viewports.

---

## 14. Seed data (synthetic only)

All names, emails and dates of birth are fictional. The Synthetic-Data Rule applies: no real or Virtusa data.

| Item | Seed |
|---|---|
| Asset classes | EQUITY (1), DEBT (2), GOLD (3), CASH (4) |
| Rule set | v1, published (§8.1) |
| Template set | v1, published (§8.4) |
| NAV | Day 0: EQUITY 150.0000, DEBT 25.0000, GOLD 50.0000, CASH 1.0000. `seed/nav_feed.csv` holds 30 further days. |
| `customer.alpha` | KYC ✓. Band MODERATE. Goals: "Home down-payment" (HOME, HIGH, 2,000,000.00, 2031-06-30) and "Retirement" (RETIREMENT, LOW, 30,000,000.00, 2050-03-31). Recommendation MODERATE/MEDIUM v1. Holdings as portfolio E1: Home = EQUITY 2000 + DEBT 8000 u, Retirement = EQUITY 2000 + DEBT 2000 + GOLD 2000 + CASH 50000 u. **This is drifted and demos rebalancing.** |
| `customer.beta` | KYC ✓. No questionnaire yet, so it demos the full journey. |
| `customer.gamma` | KYC ✗. Demos `KYC_NOT_VERIFIED`. |
| `advisor.one` | ADVISOR |
| `admin.one` | ADMIN |

The local-dev password for demo users is documented in `README.md` only. It is a dev-only synthetic credential.

---

## 15. Testing strategy and traceability

### 15.1 Test types and minimums
| Type | Location | Tool | Minimum |
|---|---|---|---|
| Unit — domain rules | `tests/unit/domain/` | pytest | ≥ 1 file per rule file in §8. Covers boundary values and rounding. |
| Unit — services | `tests/unit/service/` | pytest | Orchestration, transactions, audit writes |
| Integration — API | `tests/integration/api/` | pytest + TestClient + temp SQLite | Every endpoint, including the role matrix (401/403/404) |
| Architecture | `tests/architecture/` | pytest + import-linter | ≥ 3 required, 8 specified (§6.3) |
| E2E / UI | `tests/e2e/` | Playwright (Python) | ≥ 1 journey per role, at both viewports |
| Frontend unit | `frontend/tests/unit/` | Vitest | API client, formatters, route parsing |

- **At least 20 unit tests** in total (target ≥ 60).
- **Coverage:** ≥ 80% lines overall and ≥ 95% for `src/domain/`. `coverage.xml` is produced by `pytest --cov=src --cov-report=xml` and committed. The harness coverage ratchet must never go down.
- **Snapshots:** `tests/e2e/snapshots/` holds Playwright ARIA snapshot files (`*.aria.yml`), asserted with `to_match_aria_snapshot`, plus screenshot baselines (`*.png`) for the key screens at both viewports.
- **Determinism:** tests inject a fixed clock (2026-09-30) and a temporary DB. They never depend on wall-clock time or run order.

### 15.2 AC tagging convention
- pytest marker `ac` is registered in `pyproject.toml` and pytest runs with `--strict-markers`.
- Each AC test is decorated `@pytest.mark.ac("AC-05")` **and** its docstring starts with the ID, for example `"""AC-05.2: drift for portfolio E1."""`.
- Playwright tests follow the same convention.
- `test_ac_traceability.py` fails if any AC-01 to AC-10 has no tagged test.

### 15.3 Traceability matrix
| AC | Feature spec | Primary tests |
|---|---|---|
| AC-01 | `risk-profile_spec.md` | `unit/domain/test_risk_band_scorer.py`, `integration/api/test_risk_profile_api.py`, `e2e/test_customer_journey.py` |
| AC-02 | `recommendation_spec.md`, `admin-policy_spec.md` | `unit/domain/test_allocation_template_validator.py`, `architecture/test_allocation_sum_invariant.py` |
| AC-03 | `goal-tracker_spec.md` | `integration/api/test_goals_api.py` |
| AC-04 | `recommendation_spec.md` | `unit/domain/test_horizon_resolver.py`, `unit/domain/test_recommendation_resolver.py`, `integration/api/test_recommendation_api.py` |
| AC-05 | `holdings_spec.md` | `unit/domain/test_drift_calculator.py`, `integration/api/test_holdings_api.py` |
| AC-06 | `rebalancing_spec.md` | `unit/domain/test_drift_calculator.py`, `unit/service/test_rebalancing_service.py` |
| AC-07 | `rebalancing_spec.md` | `unit/domain/test_rebalancing_proposer.py`, `integration/api/test_rebalancing_api.py`, `e2e/test_rebalancing_journey.py` |
| AC-08 | `goal-tracker_spec.md` | `unit/domain/test_goal_progress_calculator.py`, `unit/service/test_nav_refresh_service.py` |
| AC-09 | `advisor-workbench_spec.md` | `unit/domain/test_override_policy.py`, `integration/api/test_advisor_api.py`, `architecture/test_override_requires_audit.py`, `e2e/test_advisor_journey.py` |
| AC-10 | `admin-policy_spec.md` | `unit/domain/test_version_policy.py`, `architecture/test_published_immutable.py`, `integration/api/test_admin_versioning_api.py` |

### 15.4 TDD discipline
Red → green → refactor. For each story, the failing test is committed **before** the implementation, in a separate commit. The history MUST show at least 10 test files arriving this way. `docs/tdd.md` records the approach and a worked example: the AC-02 allocation-sum invariant.

---

## 16. CI/CD and git workflow

### 16.1 GitLab CI (`.gitlab-ci.yml`)
| Stage | Job | Does |
|---|---|---|
| `install` | `deps` | `poetry install`, `npm --prefix frontend ci`, `playwright install chromium` |
| `verify` | `architecture` | `lint-imports`, plus a check that no applied migration file was modified |
| `test` | `backend-tests` | `pytest tests/unit tests/integration tests/architecture --cov=src --cov-report=xml --junitxml=report.xml`. Artefacts: `coverage.xml`, `report.xml`. Fails below the coverage thresholds in §15.1. |
| `test` | `frontend-tests` | `npm --prefix frontend test -- --run` and `npm --prefix frontend run build` |
| `e2e` | `playwright` | Starts the app and runs `pytest tests/e2e`. On failure, uploads traces and snapshots. |
| `review` | `claude-review` | **Merge-request pipelines only.** Runs Claude Code headless (`claude -p`) with a masked `ANTHROPIC_API_KEY`. It reviews the MR diff against `specs/` and the §6.3 rules and publishes the review as an MR note and a job artefact. |

The pipeline runs on merge requests and on `main`. `main` MUST stay green.

### 16.2 Git workflow
- **No direct commits to `main`.** Protect the branch.
- Branches: `sprint-<n>/<story-id>-<slug>`.
- Every change goes through an agent-reviewed merge request, merged with `git merge --no-ff`.
- At least **3** MR-driven merges are required. The target is at least one per sprint.
- Commit messages reference story and AC IDs, for example `E2-S1: drift calculator (AC-05)`.

---

## 17. Feature specs and sprint plan

### 17.1 Feature specs to author (each needs its own Acceptance Criteria section)
| File | Covers |
|---|---|
| `specs/risk-profile_spec.md` | Questionnaire, scoring, bands, effective band — AC-01, BR-01 – BR-07 |
| `specs/recommendation_spec.md` | Horizon, templates, primary goal, determinism — AC-02, AC-04, BR-08 – BR-11 |
| `specs/holdings_spec.md` | Holdings, valuation, drift, NAV feed stub — AC-05, BR-12 – BR-14, BR-25 |
| `specs/rebalancing_spec.md` | Trigger, quantities, decisions, stub orders — AC-06, AC-07, BR-15 – BR-18 |
| `specs/goal-tracker_spec.md` | Goals, progress snapshots — AC-03, AC-08, BR-19 |
| `specs/advisor-workbench_spec.md` | Portfolio view, override, manual recommendation — AC-09, BR-20 |
| `specs/admin-policy_spec.md` | Asset classes, rule-set and template versioning — AC-10, BR-21 – BR-23 |

### 17.2 Harness sprint plan
Each sprint runs generator → evaluator → ratchet → MR. Its contract goes in `sprint-contracts/` and its evaluator output in `specs/reviews/`.

| Sprint | Scope | ACs / NFRs |
|---|---|---|
| 0 — Foundation | Skeleton, config, migrations runner, append-only triggers, auth, JSON logging, `/health`, seed data, architecture tests, CI | NFR-02 – NFR-08 |
| 1 — Risk profile + recommendation | Questionnaire, scoring, goals, horizon, templates, recommendation | AC-01, AC-02, AC-03, AC-04 |
| 2 — Holdings + drift | NAV feed stub, holdings, valuation, drift | AC-05, NFR-01 |
| 3 — Rebalancing + goal tracker | Trigger, proposal, accept/dismiss, stub orders, progress snapshots | AC-06, AC-07, AC-08 |
| 4 — Advisor + admin | Override, workbench, versioning UI, in-flight rule | AC-09, AC-10 |

---

## 18. Repository deliverables checklist (capstone §7–§8)

| Deliverable | Path |
|---|---|
| Business case (problem, users, success metrics, domain rules, value proposition) | `docs/business-case.md` |
| Root + feature specs with AC sections | `specs/app_spec.md`, `specs/*_spec.md` |
| Layered CLAUDE.md (root, per module such as `src/`, `frontend/`, `tests/`, and per folder such as `src/domain/`, `migrations/`); AGENTS.md as TOC only | `CLAUDE.md`, `*/CLAUDE.md`, `AGENTS.md` |
| ≥ 3 project skills (e.g. `risk-band-scorer`, `drift-calculator`, `spec-to-test-generator`) | `.claude/skills/` |
| ≥ 2 project commands | `.claude/commands/` |
| ≥ 2 project hooks (e.g. `allocation-sum-invariant-check`, `template-immutability-check`, `pii-redaction-check`) | `.claude/hooks/` |
| ≥ 2 project agents (e.g. `risk-profiler-agent`, `rebalancing-agent`, `policy-version-validator-agent`) | `.claude/agents/` |
| Claude Agent SDK script (e.g. AC traceability auditor) | `scripts/` |
| Project plugin manifest + Playwright MCP | `plugin.json`, `.mcp.json` |
| Post-mortem / debugging log (environment-first) | `docs/post-mortems/` |
| Architecture doc with Mermaid diagrams (C4 context + risk-profile → recommendation sequence) and explicit layers | `docs/architecture.md` |
| TDD doc | `docs/tdd.md` |
| Fix-loop trace (good-to-have) | `docs/fix-loops/` |
| Knowledge deposits (good-to-have) | `docs/knowledge-deposits.md` |
| Sprint contracts and evaluator reviews | `sprint-contracts/`, `specs/reviews/` |
| Coverage artefact | `coverage.xml` |
| README quick-start (single command, demo users) | `README.md` |

---

## 19. Definition of done

A story is done when all of the following are true:
- [ ] Its ACs have tagged tests that were committed red first and are now green.
- [ ] `pytest` (unit, integration, architecture) and `lint-imports` pass, and coverage meets §15.1 without dropping below the ratchet baseline.
- [ ] No `float` in money paths, no PII in logs, no edits to applied migrations or published versions.
- [ ] Any UI change has a Playwright test at both viewports, with updated snapshots.
- [ ] The harness evaluator passes the sprint contract, and its output is committed to `specs/reviews/`.
- [ ] It was merged through an agent-reviewed MR with `--no-ff` and a green pipeline.

---

## 20. Assumptions and open questions

The capstone brief left these points open. The decisions below are made here and can be changed through a spec revision.

| # | Decision | Rationale |
|---|---|---|
| A1 | Single currency INR, amounts in paise | Multi-currency is out of scope |
| A2 | Four asset classes: EQUITY, DEBT, GOLD, CASH | Smallest realistic retail set. CASH makes rebalancing self-funding. |
| A3 | Horizon buckets at 36 and 84 months | Common short/medium/long split for goal planning |
| A4 | Portfolio target = latest recommendation, built from the primary goal | Drift needs one target per customer |
| A5 | Holdings are optionally tagged to a goal. Goal value = tagged holdings. | Makes AC-08 computable without splitting holdings across goals |
| A6 | Stub orders do not change holdings | Execution and brokerage are out of scope |
| A7 | The latest assignment wins, so a questionnaire retake can replace an override | Simplest audit-safe rule. Revisit if advisors need overrides to stick. |
| A8 | Drift threshold comes from config and is recorded on each proposal | "Configured threshold" in AC-06 |
| A9 | Stub auth with seeded users and bearer tokens | Real identity is out of scope. Only role separation is required (NFR-04). |

---

## Changelog
| Version | Date | Change |
|---|---|---|
| 1.0.0 | 2026-09-30 | Initial root spec, from BC-AINE-008 |


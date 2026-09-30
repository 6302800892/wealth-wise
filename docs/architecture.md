# WealthWise — Architecture

## 1. System context (C4 level 1)
```mermaid
C4Context
    title WealthWise — system context
    Person(customer, "Retail investor", "Profiles risk, sets goals, reviews drift, accepts or dismisses rebalancing")
    Person(advisor, "Advisor", "Reviews portfolios, overrides risk bands, logs manual recommendations")
    Person(admin, "Admin", "Publishes rule sets and allocation templates, runs the NAV refresh")
    System(wealthwise, "WealthWise", "FastAPI + React robo-advisor with deterministic, rule-based recommendations")
    System_Ext(navfeed, "NAV feed (stub)", "seed/nav_feed.csv — one synthetic price row per asset class per day")
    System_Ext(broker, "Brokerage (out of scope)", "Stub orders only; never called")
    Rel(customer, wealthwise, "Uses", "HTTPS / browser")
    Rel(advisor, wealthwise, "Uses", "HTTPS / browser")
    Rel(admin, wealthwise, "Uses", "HTTPS / browser")
    Rel(wealthwise, navfeed, "Reads daily NAV", "CSV")
    Rel(wealthwise, broker, "Would submit orders", "not implemented")
```

## 2. Containers (C4 level 2)
```mermaid
flowchart LR
    browser["Browser<br/>React SPA (frontend/dist)"] -->|"JSON over HTTP, bearer token"| api
    subgraph process["Single process — poetry run wealthwise (uvicorn)"]
        api["FastAPI app<br/>/api/v1/*, /health, static UI"]
        scheduler["NAV scheduler<br/>asyncio task (optional)"]
    end
    api --> db[("SQLite<br/>data/wealthwise.db")]
    scheduler --> db
    scheduler -->|reads| feed["seed/nav_feed.csv"]
```

## 3. Layered structure (enforced)
```mermaid
flowchart TB
    ui["UI — frontend/src (React pages, components, hooks)"]
    api["API / controllers — src/api (routers, schemas, auth guards, middleware)"]
    service["Services — src/service (use cases, transactions, audit)"]
    repository["Repositories — src/repository (sqlite3, migrations)"]
    config["Config — src/config (settings, clock, JSON logging)"]
    domain["Domain — src/domain (pure deterministic rules)"]
    types["Types — src/types (enums, value objects, fixed point, errors)"]
    ui -. HTTP only .-> api
    api --> service --> repository --> config --> domain --> types
```

| Layer | Package | Responsibility | Enforcement |
|---|---|---|---|
| Controllers | `src/api` | HTTP, validation, **authentication boundary** (`require_role`) | May not import `src.repository` (import-linter). Every non-public route is guarded (`test_routes_have_auth.py`). |
| Services | `src/service` | Orchestration, one transaction per use case, audit writes | No `fastapi` or `sqlite3` imports |
| Repositories | `src/repository` | The only `sqlite3` user. Scaled-integer storage. Append-only tables expose inserts only. | import-linter `forbidden` contracts |
| Domain | `src/domain` | Scoring, horizon, templates, drift, quantities, progress, overrides, versioning | No `logging`, `random`, `os` or I/O. No float (AST test and hook). |
| Types | `src/types` | Enums, `Decimal` helpers, records | Imports nothing internal |

## 4. Risk profile → recommendation (sequence)
```mermaid
sequenceDiagram
    autonumber
    actor C as Customer
    participant UI as React UI
    participant API as FastAPI /api/v1
    participant RP as risk_profile_service
    participant RS as recommendation_service
    participant D as domain rules
    participant DB as SQLite
    C->>UI: Answer 6 questions
    UI->>API: POST /me/risk-assessments {rule_set_version, answers}
    API->>RP: submit_assessment(user, version, answers)
    RP->>DB: active rule set version?
    alt version is not active
        RP-->>API: 409 RULE_SET_NOT_ACTIVE
    end
    RP->>D: assess(rule_set, answers) → score 16, MODERATE
    RP->>DB: INSERT risk_assessments + risk_band_assignments + audit_log (one transaction)
    API-->>UI: 201 {total_score, risk_band}
    C->>UI: Add goal (target 2036-09-30) and request a recommendation
    UI->>API: POST /me/recommendations
    API->>RS: generate(customer_id)
    RS->>D: ensure_kyc_verified, ensure_risk_band, select_primary_goal
    RS->>D: horizon_bucket(today, target) → LONG
    RS->>DB: active template set (v1)
    RS->>D: resolve_allocation(v1, MODERATE, LONG) → 60/27/10/3
    RS->>D: input_fingerprint(band, horizon, version, goal)
    alt same fingerprint as latest
        RS-->>API: 200 existing recommendation
    else new inputs
        RS->>DB: INSERT portfolio_recommendations + lines + audit_log
        RS-->>API: 201 new recommendation
    end
    API-->>UI: allocation (strings), total_pct "100.00"
```

## 5. Daily NAV refresh (sequence)
```mermaid
sequenceDiagram
    participant S as scheduler / POST /admin/nav/refresh
    participant N as nav_service
    participant G as goal_progress_service
    participant R as rebalancing_service
    participant DB as SQLite
    S->>N: run_refresh_cycle()
    N->>DB: BEGIN
    N->>DB: INSERT nav_prices (next feed date; CASH = 1.0000)
    N->>G: snapshot_all(nav_date)
    G->>DB: INSERT OR IGNORE goal_progress_snapshots (one per goal per date)
    N->>R: evaluate_all()
    loop each KYC-verified customer with holdings and a recommendation
        R->>DB: SUPERSEDE open proposals
        R->>R: drift > threshold? → propose BUY/SELL
        R->>DB: INSERT rebalancing_recommendations + lines + audit_log
    end
    N->>DB: COMMIT
```

## 6. Data model (main tables)
```mermaid
erDiagram
    customers ||--o{ users : "has login"
    customers ||--o{ risk_assessments : submits
    customers ||--o{ risk_band_assignments : "effective band = latest"
    risk_band_overrides ||--|| risk_band_assignments : "required for ADVISOR_OVERRIDE"
    customers ||--o{ goals : sets
    goals ||--o{ holdings : "tags (optional)"
    goals ||--o{ goal_progress_snapshots : "one per nav_date"
    customers ||--o{ portfolio_recommendations : receives
    allocation_template_set_versions ||--o{ allocation_template_rows : contains
    portfolio_recommendations ||--o{ portfolio_recommendation_lines : "target snapshot"
    portfolio_recommendations ||--o{ rebalancing_recommendations : "drift baseline"
    rebalancing_recommendations ||--o{ rebalancing_lines : proposes
    rebalancing_recommendations ||--o| rebalancing_decisions : "at most one"
    rebalancing_recommendations ||--o{ stub_orders : "on accept"
```
**Append-only** (UPDATE and DELETE triggers abort): assessments, assignments, overrides, recommendations and lines, NAV prices, snapshots, rebalancing proposals, lines, decisions and stub orders, manual recommendations, `audit_log`, `schema_migrations`. **Immutable once published:** rule-set and template versions and their rows.

## 7. Cross-cutting decisions
| Concern | Decision | Why |
|---|---|---|
| Fixed point (NFR-01) | `Decimal` in Python. Integers in SQLite (paise, bp, ×10⁴). Strings on the wire. Basis points in JS. | Exact sums (100.00) and reproducible rounding |
| Determinism | Injected `Clock`. No randomness in the domain. Input fingerprints. | The same inputs always produce the same advice |
| Auth (NFR-04) | Stub PBKDF2 users with opaque bearer tokens. One role per user. | Real identity is out of scope, but role separation is required |
| Logging (NFR-03, NFR-06) | JSON lines with `correlation_id`. A denylist drops PII and balance keys. | Observability without leaking customer data |
| Migrations (NFR-05) | Numbered SQL, checksummed. The runner refuses to start if an applied file changed. | Tamper-evident schema history |
| Single command | `poetry run wealthwise` builds the UI if needed and serves API + UI on :8000 | One origin, no CORS, simple local deployment |

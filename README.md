# WealthWise — Robo-Advisory & Portfolio Recommendation Platform

AI-Native Engineer capstone **BC-AINE-008** (BFS / Wealth Management). Customers:
1. take a risk questionnaire and get a deterministic risk band
2. set goals
3. receive a rule-based allocation from a versioned template
4. see drift against that allocation
5. accept or dismiss rebalancing proposals

Advisors override bands with a full audit trail. Admins publish immutable versions of rules and templates.

Claude Code agents built the platform on the **Claude Harness Engine**, under the rules in [CLAUDE.md](CLAUDE.md). All data is synthetic.

## Quick start
Prerequisites:
- Python **3.12+**. On Windows use `py -3.13`.
- [Poetry](https://python-poetry.org/)
- Node.js **20+** with npm. It builds the UI and runs the Claude Code hooks.

```bash
poetry install                      # Python deps (add --with agents for the Agent SDK script)
poetry run wealthwise               # single command: migrate + seed + build UI (first run) + serve
```
Open **http://127.0.0.1:8000**. Health check: `GET /health`.

### Demo users (synthetic; local-dev password `WealthWise@2026`)
| Username | Role | What to try |
|---|---|---|
| `customer.alpha` | Customer | Drifted portfolio (EQUITY 60% vs 50% target). Open **Rebalancing** → accept. |
| `customer.beta` | Customer | New customer. **Risk profile** → **Goals** → **Recommendation**. |
| `customer.gamma` | Customer | KYC pending, so recommendations are blocked. |
| `advisor.one` | Advisor | Open a customer → override the risk band → see the audit trail. |
| `admin.one` | Admin | **Templates** → new draft → try a row summing to 99% → fix → publish. **NAV feed** → run refresh. |

### Configuration (environment variables)
| Variable | Default | Purpose |
|---|---|---|
| `WEALTHWISE_DB_PATH` | `data/wealthwise.db` | SQLite file |
| `WEALTHWISE_DRIFT_THRESHOLD_PCT` | `5.00` | Rebalancing trigger (strictly greater than) |
| `WEALTHWISE_NAV_REFRESH_INTERVAL_SECONDS` | `0` (off) | Automatic daily-NAV refresh schedule |
| `WEALTHWISE_BUSINESS_DATE` | today | Pin the business date, for example `2026-09-30`, for demos and E2E |
| `WEALTHWISE_PORT` / `WEALTHWISE_HOST` | `8000` / `127.0.0.1` | Server bind |
| `WEALTHWISE_DEMO_PASSWORD` | `WealthWise@2026` | Password given to seeded users |

## Tests
```bash
poetry run pytest --cov=src --cov-report=xml      # unit + integration + architecture (writes coverage.xml)
poetry run lint-imports                            # layering contracts
npm --prefix frontend ci && npm --prefix frontend test -- --run
npm --prefix frontend run build && poetry run playwright install chromium
poetry run pytest tests/e2e -m e2e                 # Playwright journeys at 1280px and 375px
```

## Repository map
| Path | Contents |
|---|---|
| `specs/` | `app_spec.md` (root), 7 feature specs, `features.json`, `reviews/` (evaluator output) |
| `sprint-contracts/` | Harness sprint contracts 0–6 |
| `src/` | FastAPI backend: `types → domain → config → repository → service → api` |
| `migrations/` | Append-only, checksum-verified SQL (schema + policy seeds) |
| `frontend/` | React (JSX) + Vite UI |
| `tests/` | pytest unit, integration, architecture and E2E (Playwright + ARIA snapshots) |
| `.claude/` | Harness foundation plus WealthWise agents, skills, commands and hooks |
| `scripts/` | Contract evaluator, Claude Agent SDK reviewer, traceability tools |
| `docs/` | Business case, architecture (Mermaid), TDD, knowledge deposits, fix loops, post-mortems |
| `plugin.json`, `.mcp.json` | WealthWise substrate plugin, Playwright MCP |
| `.gitlab-ci.yml` | Build/test/E2E pipeline plus the Claude Code merge-request review |

See [AGENTS.md](AGENTS.md) for a full table of contents.

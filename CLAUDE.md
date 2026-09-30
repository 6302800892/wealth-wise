# WealthWise — root context for Claude Code

Robo-advisory platform (BC-AINE-008): risk profiling → rule-based allocation → goal tracking → drift-triggered rebalancing. **Recommendation logic is deterministic and rule-based. No ML, no randomness.**

## Ground rules (from the capstone brief)
1. **No hand-coding.** Agents generate all production code, tests and migrations. Humans edit only specs, CLAUDE.md files, agents, skills, hooks and commands.
2. **Spec-is-truth.** `specs/app_spec.md` wins over code. Change behaviour by amending the spec (version and changelog) and then regenerating.
3. **PR-only.** No direct commits to `main`. Work on `sprint-N/<slug>` or `fix/<id>`, and merge through an MR with `git merge --no-ff`.
4. **Synthetic data only.** Never use real customer or Virtusa data.

## Stack (fixed; see spec §5)
Python 3.12+ · FastAPI · SQLite (stdlib `sqlite3`) · Poetry · pytest + pytest-cov · import-linter · React (JSX) + Vite · Vitest · Playwright (Python) · GitLab CI · Playwright MCP · Claude Harness Engine.
Not allowed: ORMs, Alembic, TypeScript, router or UI libraries, Docker, ruff/mypy/uv, and **floats for money**.

## Commands
| Task | Command |
|---|---|
| Run the app (API + UI on :8000, seeded) | `poetry run wealthwise` |
| Backend tests + coverage | `poetry run pytest --cov=src --cov-report=xml` |
| Layering contracts | `poetry run lint-imports` |
| Frontend unit tests / build | `npm --prefix frontend test -- --run` · `npm --prefix frontend run build` |
| E2E (needs the build) | `poetry run pytest tests/e2e -m e2e` |
| Sprint evaluation | `/sprint-evaluate <n>` · AC coverage: `/ac-trace` |

## Architecture (one-way imports, enforced)
`src/api` → `src/service` → `src/repository` → `src/config` → `src/domain` → `src/types`.
Each folder has its own `CLAUDE.md` with local rules. Read it before editing there.

| Folder | Context file |
|---|---|
| `src/` | [src/CLAUDE.md](src/CLAUDE.md) |
| `src/domain/` | [src/domain/CLAUDE.md](src/domain/CLAUDE.md) |
| `src/service/` | [src/service/CLAUDE.md](src/service/CLAUDE.md) |
| `src/repository/` | [src/repository/CLAUDE.md](src/repository/CLAUDE.md) |
| `src/api/` | [src/api/CLAUDE.md](src/api/CLAUDE.md) |
| `migrations/` | [migrations/CLAUDE.md](migrations/CLAUDE.md) |
| `tests/` | [tests/CLAUDE.md](tests/CLAUDE.md) |
| `tests/e2e/` | [tests/e2e/CLAUDE.md](tests/e2e/CLAUDE.md) |
| `frontend/` | [frontend/CLAUDE.md](frontend/CLAUDE.md) |

## Invariants you must never break
- Money, units, NAV and percentages are `Decimal` in Python, scaled integers in SQLite, and strings on the wire (NFR-01).
- Append-only tables are insert-only (NFR-02). Published policy versions are immutable (AC-10).
- No PII or balances in logs (NFR-03). Every non-public route has a role guard (NFR-04).
- Applied migrations are never edited (NFR-05). Every template row sums to 100.00 (AC-02).
- Every AC has tagged tests (`@pytest.mark.ac("AC-NN")`), written red-first.

## Local environment (Windows workstation; PM-001)
- Use `py -3.13` or `.venv/Scripts/python`. The PATH `python` is 3.8.
- Node lives under `%LOCALAPPDATA%\Microsoft\WinGet\Packages\OpenJS.NodeJS.LTS_*`. Hooks need `node` on PATH.
- Hooks read stdin via `fs.readFileSync(0)`, never `/dev/stdin`, which silently fails on Windows.
- Git Bash rewrites leading-slash arguments. Prefer `git sparse-checkout --cone` or set `MSYS_NO_PATHCONV=1`.

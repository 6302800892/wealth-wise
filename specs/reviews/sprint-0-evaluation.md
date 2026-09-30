# Evaluator review — Sprint 0 (Foundation)

| Field | Value |
|---|---|
| Contract | `sprint-contracts/sprint-0.json` |
| Branch | `sprint-0/foundation` |
| Date | 2026-09-30 |
| Verdict | **PASS** — ratchet advanced |

## Layer 1 — Tests
- `pytest`: **62 passed**, 0 failed
- Coverage (`src/`): **82%** (baseline set to 82)
- Red → green: failing tests committed in `test(sprint-0): add failing foundation tests (red)` before the implementation commit.

## Layer 2 — Live API checks
Ran `python scripts/evaluate_contract.py sprint-contracts/sprint-0.json --start` against a temporary server. Result: **5/5 PASS**. See `sprint-0-api-evaluation.md`.

## Layer 3 — Architecture
| Check | Result |
|---|---|
| import-linter: 5 contracts | KEPT |
| A probe `import logging` in `src/domain` breaks the purity contract | Detected (contract BROKEN), then the probe was removed |
| No float literals or calls in types/domain/repository/service | PASS |
| `audit_log`, `schema_migrations` reject UPDATE/DELETE | PASS |
| Every non-public operation returns 401 without a token; wrong roles get 403 | PASS |

## Findings
1. **Fixed during sprint.** The `forbidden` import contracts reported indirect imports, for example `api → service → repository`, which is legitimate. They now use `allow_indirect_imports = true`, so only direct imports are forbidden. The layers contract still covers indirect upward imports.
2. **Fixed during sprint.** FastAPI 0.142 nests included routers (`_IncludedRouter`), so route introspection found no routes. The auth-boundary test is now behavioural: it calls every OpenAPI operation, which is more robust than relying on private internals. Logged in `docs/knowledge-deposits.md`.

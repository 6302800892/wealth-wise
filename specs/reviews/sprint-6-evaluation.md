# Evaluator review — Sprint 6 (AI-native substrate, CI/CD, documentation)

| Field | Value |
|---|---|
| Contract | `sprint-contracts/sprint-6.json` |
| Branch | `sprint-6/substrate-ci-docs` |
| Verdict | **PASS**. Coverage 94% (ratchet held), domain 97% |

## Layer 1 — Tests
- `pytest` with Node on PATH: **303 passed**, including 7 hook tests that execute the real Claude Code hooks.
- Vitest: **15 passed**. Playwright E2E: **25 passed, 3 skipped**. `lint-imports`: 5 contracts kept.
- Regression: all sprint contracts re-run against fresh servers, **42/42 API checks PASS** (sprints 0–5).
- `poetry run wealthwise` smoke test: migrations 10/10, seed loaded, `/health` 200, UI served at `/`.

## Layer 2 — Substrate checks
| Item | Required | Delivered | Evidence |
|---|---|---|---|
| Project agents | 2 | 5 | `.claude/agents/{risk-profiler,rebalancing,policy-version-validator,archtest-author}-agent.md`, `doc-writer.md` |
| Project skills | 3 | 5 | `.claude/skills/{risk-band-scorer,drift-calculator,rebalancing-quantity-proposer,policy-version-validator,spec-to-test-generator}` |
| Project commands | 2 | 3 | `/ac-trace`, `/sprint-evaluate`, `/new-template-version` |
| Project hooks | 2 | 4 | Each proven to block a violation *and* pass all of `src/` (`test_substrate_hooks.py`) |
| Agent SDK script | 1 | 1 | `scripts/ac_trace_agent.py` (`query()` + `ClaudeAgentOptions`, read-only tools plus one report). `--dry-run` verified. |
| Plugin / MCP | yes | yes | `plugin.json`, `.claude/hooks/wealthwise-hooks.json`, `.mcp.json`, evaluator granted `mcp__playwright__*` |
| CI | yes | yes | `.gitlab-ci.yml`: architecture, migrations-append-only, backend-tests (cobertura), frontend-tests, playwright-e2e, claude-review |
| Traceability | all ACs | 10/10 ACs, 48/48 scenarios | `specs/reviews/ac-traceability.md`, `specs/features.json` |

## Findings
1. **Critical, fixed (PM-001).** All 15 harness hooks read `/dev/stdin`, which does not exist for Node on Windows, so every guardrail silently passed. They were switched to `readFileSync(0)`. `protect-env` now blocks `.env` writes (exit 2).
2. **Fixed.** `src/main.py` logged a `reason` key, which the new PII hook flags. It was renamed to `cause`.
3. **Cleanup.** The unused `nav_state_path` setting was removed (KD-04).
4. **Spec amended to v1.1.0** for FL-001 (BR-21). Feature specs were regenerated from the root spec so AC text cannot drift.
5. **Not verifiable locally.** The `claude-review` CI job needs `ANTHROPIC_API_KEY` in GitLab and only runs on merge-request pipelines. The Agent SDK script was dry-run only, to avoid spending the user's API quota.

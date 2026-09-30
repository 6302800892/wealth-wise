# Evaluator review — Sprint 5 (Frontend + UI validation)

| Field | Value |
|---|---|
| Contract | `sprint-contracts/sprint-5.json` |
| Branch | `sprint-5/frontend-e2e` |
| Verdict | **PASS** |

## Layer 1 — Tests
- Vitest (`frontend/tests/unit`): **15 passed**. These cover fixed-point display helpers, hash routing and role navigation, and the API client error envelope. They were committed red before the implementation.
- pytest (backend): **295 passed** (E2E deselected by default).
- Playwright E2E (`pytest tests/e2e -m e2e`): **25 passed, 3 skipped**. The skips are journeys that intentionally run on one viewport only, such as global template publishing. A second run matched the committed ARIA baselines.

## Layer 2 — Live checks
- API: **2/2 PASS** with the built UI mounted at `/`.
- Playwright checks pw-501 to pw-506: PASS at 1280×800 and 375×812. The evaluator drove the real UI through Chromium with the pytest-playwright suite, which is the same browser engine the Playwright MCP server uses.

## Layer 3 — Design review (design-critic rubric)
| Criterion | Score | Notes |
|---|---|---|
| Visual hierarchy | 8 | One primary action per card. Stat tiles lead each page. |
| Accessibility | 7 | Labelled inputs, `aria-expanded` on the menu toggle, `role=alert` errors, semantic tables. |
| Responsiveness | 8 | Below 640px the nav collapses and tables become labelled cards (screenshots in `tests/e2e/snapshots/screenshots/`). |
| Interaction feedback | 7 | Disabled buttons while busy, error envelope codes shown, success notices. |

## Findings
1. **Fixed.** ARIA snapshots differ between viewports because the phone layout hides `thead`. Baselines are now stored per viewport. Knowledge deposit KD-06.
2. **Fixed.** A dashboard progress width used `Number()` on a percentage string. It was replaced with `capPct()`, which works in integer basis points, so the UI does no float arithmetic on financial values (NFR-01).
3. **Process note.** The E2E journeys were written after the pages, not before. This is recorded honestly in `docs/tdd.md`. The unit layers followed red → green.

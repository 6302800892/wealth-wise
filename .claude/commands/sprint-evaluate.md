---
name: sprint-evaluate
description: Evaluate a WealthWise sprint contract end-to-end (tests, coverage ratchet, live API checks, Playwright journeys) and write the evaluator review.
argument-hint: "<sprint-number>"
---

# /sprint-evaluate — Run the three-layer evaluation for sprint $ARGUMENTS

1. **Contract.** Read `sprint-contracts/sprint-$ARGUMENTS.json`. If it is missing, stop and ask the user to create it (see `.claude/templates/sprint-contract.json`).
2. **Layer 1: tests and ratchet.**
   ```bash
   python -m pytest --cov=src --cov-report=xml -q
   lint-imports
   ```
   Compare the coverage `TOTAL` with `.claude/state/coverage-baseline.txt`. **FAIL** if it is lower (ratchet). On PASS, write the new value.
3. **Layer 2: live API checks.**
   ```bash
   python scripts/evaluate_contract.py sprint-contracts/sprint-$ARGUMENTS.json --start
   ```
   This writes `specs/reviews/sprint-$ARGUMENTS-api-evaluation.md`.
4. **Layer 3: UI.** If the contract has `playwright_checks`:
   ```bash
   npm --prefix frontend run build && python -m pytest tests/e2e -m e2e -q
   ```
   Also use the Playwright MCP server (`.mcp.json`) to open `http://127.0.0.1:8000` and spot-check each `pw-*` description at 1280px and 375px.
5. **Review.** Write `specs/reviews/sprint-$ARGUMENTS-evaluation.md` with a verdict, a layer-by-layer evidence table and numbered findings. Append an entry to `.claude/state/iteration-log.md`, which is append-only.
6. **Gate.** Only on PASS may the branch be merged, with `git merge --no-ff`, through an MR.

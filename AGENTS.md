# AGENTS.md — table of contents

This file is an index only. Instructions live in the linked files.

## Context
- [CLAUDE.md](CLAUDE.md): root rules, commands, architecture
- [src/CLAUDE.md](src/CLAUDE.md) · [src/domain/CLAUDE.md](src/domain/CLAUDE.md) · [src/service/CLAUDE.md](src/service/CLAUDE.md) · [src/repository/CLAUDE.md](src/repository/CLAUDE.md) · [src/api/CLAUDE.md](src/api/CLAUDE.md)
- [migrations/CLAUDE.md](migrations/CLAUDE.md) · [tests/CLAUDE.md](tests/CLAUDE.md) · [tests/e2e/CLAUDE.md](tests/e2e/CLAUDE.md) · [frontend/CLAUDE.md](frontend/CLAUDE.md)

## Specifications
- [specs/app_spec.md](specs/app_spec.md): root spec (AC-01 – AC-10, NFR-01 – NFR-08, BR-01 – BR-25)
- Features: [risk-profile](specs/risk-profile_spec.md) · [recommendation](specs/recommendation_spec.md) · [holdings](specs/holdings_spec.md) · [rebalancing](specs/rebalancing_spec.md) · [goal-tracker](specs/goal-tracker_spec.md) · [advisor-workbench](specs/advisor-workbench_spec.md) · [admin-policy](specs/admin-policy_spec.md)
- [specs/features.json](specs/features.json) · [specs/reviews/](specs/reviews/) · [sprint-contracts/](sprint-contracts/)

## Agents (`.claude/agents/`)
| Agent | Kind | Source |
|---|---|---|
| planner, generator, evaluator, test-engineer, security-reviewer, ui-designer, design-critic | base | Claude Harness Engine |
| [risk-profiler-agent](.claude/agents/risk-profiler-agent.md) | domain | WealthWise |
| [rebalancing-agent](.claude/agents/rebalancing-agent.md) | domain | WealthWise |
| [policy-version-validator-agent](.claude/agents/policy-version-validator-agent.md) | technical | WealthWise |
| [archtest-author-agent](.claude/agents/archtest-author-agent.md) | technical | WealthWise |
| [doc-writer](.claude/agents/doc-writer.md) | bonus | WealthWise |

## Skills (`.claude/skills/`)
- WealthWise: [risk-band-scorer](.claude/skills/risk-band-scorer/SKILL.md) · [drift-calculator](.claude/skills/drift-calculator/SKILL.md) · [rebalancing-quantity-proposer](.claude/skills/rebalancing-quantity-proposer/SKILL.md) · [policy-version-validator](.claude/skills/policy-version-validator/SKILL.md) · [spec-to-test-generator](.claude/skills/spec-to-test-generator/SKILL.md)
- Harness: architecture, auto, brd, build, code-gen, deploy, design, evaluate, evaluation, fix-issue, implement, improve, lint-drift, refactor, review, spec, test, testing

## Commands (`.claude/commands/`)
- WealthWise: [/ac-trace](.claude/commands/ac-trace.md) · [/sprint-evaluate](.claude/commands/sprint-evaluate.md) · [/new-template-version](.claude/commands/new-template-version.md)
- Harness: [/scaffold](.claude/commands/scaffold.md)

## Hooks (`.claude/hooks/`, registered in `.claude/settings.json`)
- WealthWise: allocation-sum-invariant-check · migration-append-only-check · pii-log-check · no-float-money-check
- Harness: check-architecture · check-file-length · check-function-length · detect-secrets · enforce-length-pre · lint-on-save · pre-commit-gate · protect-env · require-review · scope-directory · sprint-contract-gate · task-completed · teammate-idle-check · track-writes · typecheck

## Packaging and tooling
- [plugin.json](plugin.json) (WealthWise substrate) · [.claude/.claude-plugin/plugin.json](.claude/.claude-plugin/plugin.json) (harness) · [.mcp.json](.mcp.json) (Playwright MCP) · [project-manifest.json](project-manifest.json)
- Scripts: [evaluate_contract.py](scripts/evaluate_contract.py) · [ac_trace_agent.py](scripts/ac_trace_agent.py) (Claude Agent SDK) · [ac_trace_report.py](scripts/ac_trace_report.py) · [generate_features.py](scripts/generate_features.py) · [check_migrations_append_only.py](scripts/check_migrations_append_only.py)

## Docs
- [business-case](docs/business-case.md) · [architecture](docs/architecture.md) · [tdd](docs/tdd.md) · [knowledge-deposits](docs/knowledge-deposits.md) · [fix-loops/](docs/fix-loops/) · [post-mortems/](docs/post-mortems/)

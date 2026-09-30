"""Programmatic Claude Agent SDK usage: an AC-scenario coverage reviewer.

The agent reads the Given-When-Then scenarios in specs/app_spec.md §9, searches tests/ for each scenario,
judges whether the test actually asserts the scenario's "then" clause (not just that a tag exists), and
writes specs/reviews/ac-scenario-review.md. It may only read files and write that one report.

Usage:
    poetry install --with agents
    poetry run python scripts/ac_trace_agent.py            # runs the agent (needs Claude Code auth / ANTHROPIC_API_KEY)
    poetry run python scripts/ac_trace_agent.py --dry-run  # prints the configuration without calling the model
"""

import argparse
import asyncio
import sys
from pathlib import Path

from claude_agent_sdk import AssistantMessage, ClaudeAgentOptions, ResultMessage, TextBlock, query

ROOT = Path(__file__).resolve().parents[1]
REPORT = "specs/reviews/ac-scenario-review.md"

SYSTEM_PROMPT = """You are the WealthWise acceptance-criteria reviewer, a skeptical QA engineer.
Rules: never modify source or tests; the spec (specs/app_spec.md) is the source of truth; money values are
decimal strings; cite file paths and test names for every claim."""

TASK = f"""Review acceptance-criteria coverage for WealthWise.

1. Read specs/app_spec.md section 9 and list every scenario id (AC-NN.n) with its Then clause.
2. For each scenario, Grep tests/ for the id and read the matching test.
3. Classify each scenario: COVERED (assertions match the Then clause), WEAK (tagged but assertions are
   partial) or MISSING (no test references it).
4. Write {REPORT} with a summary line, a table (scenario | verdict | test | note) and a short list of the
   three most valuable tests to add. Keep it under 150 lines."""


def build_options() -> ClaudeAgentOptions:
    return ClaudeAgentOptions(
        system_prompt=SYSTEM_PROMPT,
        allowed_tools=["Read", "Grep", "Glob", "Write"],
        permission_mode="acceptEdits",
        cwd=str(ROOT),
        max_turns=40,
    )


async def run_review() -> int:
    exit_code = 0
    async for message in query(prompt=TASK, options=build_options()):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(block.text)
        elif isinstance(message, ResultMessage):
            cost = f"${message.total_cost_usd:.4f}" if message.total_cost_usd is not None else "n/a"
            print(f"\n[agent finished] turns={message.num_turns} cost={cost} error={message.is_error}")
            exit_code = 1 if message.is_error else 0
    return exit_code


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--dry-run", action="store_true", help="print the agent configuration and exit")
    args = parser.parse_args()
    if args.dry_run:
        options = build_options()
        print(f"cwd={options.cwd}\nallowed_tools={options.allowed_tools}\nmax_turns={options.max_turns}\n")
        print(TASK)
        return 0
    return asyncio.run(run_review())


if __name__ == "__main__":
    sys.exit(main())

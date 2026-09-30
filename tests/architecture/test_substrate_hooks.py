"""The project's Claude Code hooks block what they claim to block — and pass the real codebase."""

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

from src.config.settings import PROJECT_ROOT

HOOKS = PROJECT_ROOT / ".claude" / "hooks"
NODE = os.environ.get("NODE_BINARY") or shutil.which("node")
pytestmark = pytest.mark.skipif(NODE is None, reason="node is required to run Claude Code hooks")


def _run(hook: str, file_path: Path) -> subprocess.CompletedProcess:
    payload = json.dumps({"tool_name": "Write", "tool_input": {"file_path": str(file_path)}})
    return subprocess.run([NODE, str(HOOKS / hook)], input=payload, capture_output=True, text=True,
                          cwd=PROJECT_ROOT, check=False)


def _write(tmp_path: Path, relative: str, content: str) -> Path:
    path = tmp_path / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


@pytest.mark.ac("AC-02")
def test_allocation_sum_hook_blocks_rows_not_totalling_100(tmp_path):
    """AC-02: a seeded row of 9 999 bp is blocked with exit code 2."""
    sql = ("INSERT INTO allocation_template_rows VALUES (3, 'MODERATE', 'SHORT', 'EQUITY', 5000),"
           " (3, 'MODERATE', 'SHORT', 'DEBT', 4999);")
    result = _run("allocation-sum-invariant-check.js", _write(tmp_path, "migrations/0099_bad.sql", sql))
    assert result.returncode == 2
    assert "v3 MODERATE/SHORT: 9999 bp" in result.stderr


def test_allocation_sum_hook_accepts_the_real_seed():
    assert _run("allocation-sum-invariant-check.js", PROJECT_ROOT / "migrations" / "0005_seed_template_set_v1.sql").returncode == 0


def test_migration_hook_blocks_committed_files_and_allows_new_ones(tmp_path):
    committed = _run("migration-append-only-check.js", PROJECT_ROOT / "migrations" / "0001_core_schema.sql")
    assert committed.returncode == 2 and "append-only" in committed.stderr
    fresh = _run("migration-append-only-check.js", _write(tmp_path, "migrations/0999_new_change.sql", "SELECT 1;"))
    assert fresh.returncode == 0


def test_pii_hook_blocks_sensitive_log_fields(tmp_path):
    source = 'log.info("goal_created", extra={"goal_id": gid, "target_amount": amount})\nlog.info(f"hi {name}")\n'
    result = _run("pii-log-check.js", _write(tmp_path, "src/service/bad.py", source))
    assert result.returncode == 2
    assert "target_amount" in result.stderr and "f-string" in result.stderr


def test_no_float_hook_blocks_float_but_not_decimal_strings(tmp_path):
    bad = _run("no-float-money-check.js", _write(tmp_path, "src/domain/bad.py", "rate = 0.05\nx = float(y)\n"))
    assert bad.returncode == 2 and "line 1" in bad.stderr and "line 2" in bad.stderr
    good = _run("no-float-money-check.js", _write(tmp_path, "src/domain/good.py", 'RATE = Decimal("0.05")  # 0.05\n'))
    assert good.returncode == 0


@pytest.mark.parametrize("hook", ["pii-log-check.js", "no-float-money-check.js"])
def test_hooks_pass_every_production_file(hook):
    failures = []
    for path in sorted((PROJECT_ROOT / "src").rglob("*.py")):
        result = _run(hook, path)
        if result.returncode != 0:
            failures.append(result.stderr)
    assert failures == []

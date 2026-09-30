"""Traceability: every AC-NN in specs/app_spec.md has at least one test marked @pytest.mark.ac("AC-NN")."""

import ast
import re

from src.config.settings import PROJECT_ROOT

AC_PATTERN = re.compile(r"^### (AC-\d{2}) ", re.MULTILINE)


def _spec_acs() -> set[str]:
    return set(AC_PATTERN.findall((PROJECT_ROOT / "specs" / "app_spec.md").read_text(encoding="utf-8")))


def _tagged_acs() -> dict[str, int]:
    counts: dict[str, int] = {}
    for path in (PROJECT_ROOT / "tests").rglob("test_*.py"):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if (isinstance(node, ast.Call) and getattr(node.func, "attr", None) == "ac"
                    and node.args and isinstance(node.args[0], ast.Constant)):
                counts[node.args[0].value] = counts.get(node.args[0].value, 0) + 1
    return counts


def test_spec_defines_ten_acceptance_criteria():
    assert _spec_acs() == {f"AC-{n:02d}" for n in range(1, 11)}


def test_every_acceptance_criterion_has_a_tagged_test():
    tagged = _tagged_acs()
    missing = sorted(ac for ac in _spec_acs() if tagged.get(ac, 0) == 0)
    assert missing == [], f"ACs without tests: {missing}"


def test_tags_reference_only_known_criteria():
    unknown = sorted(set(_tagged_acs()) - _spec_acs())
    assert unknown == []

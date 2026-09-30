"""NFR-01: no floating-point arithmetic in money paths (AST scan)."""

import ast

import pytest

from src.config.settings import PROJECT_ROOT

SCANNED_LAYERS = ["types", "domain", "repository", "service"]


def _python_files():
    for layer in SCANNED_LAYERS:
        yield from sorted((PROJECT_ROOT / "src" / layer).rglob("*.py"))


def _float_usages(path):
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            yield node.lineno, "float literal"
        if isinstance(node, ast.Name) and node.id == "float":
            yield node.lineno, "float() / float annotation"


@pytest.mark.parametrize("path", list(_python_files()), ids=lambda p: str(p.relative_to(PROJECT_ROOT)))
def test_no_float_in_money_layers(path):
    usages = list(_float_usages(path))
    assert usages == [], f"{path}: {usages}"


def test_scan_covers_files():
    assert len(list(_python_files())) > 5

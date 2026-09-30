"""NFR-08: layering rules are enforced by import-linter contracts (pyproject.toml)."""

import subprocess
import sys
from pathlib import Path

from src.config.settings import PROJECT_ROOT

LAYERS = ["types", "domain", "config", "repository", "service", "api"]


def test_import_linter_contracts_pass():
    lint_imports = Path(sys.executable).parent / "lint-imports"
    result = subprocess.run(
        [str(lint_imports)], cwd=PROJECT_ROOT, capture_output=True, text=True, check=False
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_every_layer_package_exists():
    for layer in LAYERS:
        assert (PROJECT_ROOT / "src" / layer / "__init__.py").is_file(), f"missing layer src/{layer}"


def test_layers_contract_matches_documented_order():
    pyproject = (PROJECT_ROOT / "pyproject.toml").read_text()
    expected = ",\n    ".join(f'"src.{layer}"' for layer in reversed(LAYERS))
    assert expected in pyproject

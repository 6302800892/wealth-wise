"""CI guard for NFR-05: a merge request may only ADD migration files, never modify, rename or delete them.

Usage: python scripts/check_migrations_append_only.py [base-ref]   (default: origin/main)
"""

import subprocess
import sys


def main() -> int:
    base = sys.argv[1] if len(sys.argv) > 1 else "origin/main"
    result = subprocess.run(
        ["git", "diff", "--name-status", f"{base}...HEAD", "--", "migrations/"],
        capture_output=True, text=True, check=False,
    )
    if result.returncode != 0:
        print(f"cannot diff against {base}: {result.stderr.strip()}")
        return 2
    violations = [line for line in result.stdout.splitlines() if line and line[0] in "MDR"]
    for line in violations:
        print(f"NFR-05 violation (migrations are append-only): {line}")
    if not violations:
        print(f"migrations append-only check passed against {base}")
    return 1 if violations else 0


if __name__ == "__main__":
    sys.exit(main())

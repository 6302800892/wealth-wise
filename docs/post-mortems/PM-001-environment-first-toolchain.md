# PM-001 — Toolchain and environment issues on the Windows workstation (environment-first resolution)

| Field | Value |
|---|---|
| Date | 2026-09-30 |
| Impact | Silent: guardrail hooks were no-ops, and some scripts crashed. No production code defect. |
| Detection | During setup, and while testing the new project hooks |
| Resolution principle | **Environment first.** Check interpreter, PATH, shell and encoding before suspecting the code. |

## Timeline and findings
| # | Symptom | Environment check (first) | Root cause | Resolution |
|---|---|---|---|---|
| 1 | `python --version` → 3.8.10, but the stack needs 3.12+ (StrEnum, `datetime.UTC`) | `py -0p` listed the installed interpreters | PATH puts a legacy 3.8 first. 3.13 exists only through the `py` launcher. | The project venv was created with `py -3.13 -m venv .venv`, and every command uses `.venv/Scripts/python`. |
| 2 | `poetry`, `node` and `npm` not found | `command -v` for each tool | Not installed | Poetry went into its own tool venv (`~/.poetry-tool`), not the project venv. Node 24 LTS came from `winget --scope user`. |
| 3 | `git sparse-checkout set "/.claude/"` checked out **nothing** | Compared the pattern stored in `.git/info/sparse-checkout` | MSYS path conversion rewrote `/.claude/` to `C:/Program Files/Git/.claude/` | Cone mode: `git sparse-checkout set --cone .claude`. KD-10. |
| 4 | Hooks never blocked anything. `protect-env` let a `.env` write through (exit 0). | Ran a hook by hand with piped JSON: `node -e "readFileSync('/dev/stdin')"` → `ENOENT` | `/dev/stdin` does not exist for Node on Windows. The harness wraps the read in `try/catch` → `exit 0`. | Replaced the read with `fs.readFileSync(0, 'utf8')` in all 15 harness hooks. `protect-env` now exits 2. KD-08. |
| 5 | `evaluate_contract.py` crashed: `UnicodeEncodeError: 'charmap' codec can't encode '\u2192'` | Checked `sys.stdout.encoding` → cp1252 | The Windows console code page is not UTF-8 | Write report bytes directly. `PYTHONUTF8=1` in CI. KD-09. |
| 6 | `lint-on-save` / `typecheck` hooks would call `uv run ruff` / `uv run mypy` | Read the hook source: missing manifest ⇒ ruff/mypy fallback | Harness defaults assume uv, ruff and mypy, none of which are in the approved stack | `project-manifest.json` sets `"linter": "none"` and `"typechecker": "none"`, so those hooks skip. |

## Why environment-first mattered
Items 3 and 4 looked like logic bugs: an empty checkout, and hooks that "don't work". In both cases, reading the code would have wasted time. The code was correct for Linux, and the **environment** was different. A 30-second reproduction outside the tool, running Node directly with piped JSON, isolated each cause.

## Prevention
- `tests/architecture/test_substrate_hooks.py` runs every project hook with real JSON on stdin and asserts it blocks. A silent no-op now fails the suite, and CI installs Node for this.
- README quick-start pins the interpreter (`py -3.13`) and lists the required tools.
- `CLAUDE.md` (root) has a *Local environment* section with the Windows specifics above.

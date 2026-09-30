# src/ — backend package (`src`)

- Python package imported as `src.<layer>`. The harness `check-architecture` hook and import-linter both rely on this.
- Layer order (a module may import only from layers below it): `api` → `service` → `repository` → `config` → `domain` → `types`.
- `src/main.py` is the composition root. It is the only place that wires everything, and it serves the built UI.
- Every new module goes into exactly one layer folder. If you cannot decide where it belongs, it is probably doing two jobs, so split it.
- Harness limits: aim for ≤ 200 lines per file (hard limit 300) and ≤ 50 lines per function.
- Run `lint-imports` after adding imports across layers.

# tests/ — test suite

| Folder | What | Fixtures |
|---|---|---|
| `unit/domain/` | pure rules, worked examples, boundaries | `tests/factories.py` |
| `unit/service/` | orchestration, refresh cycle, thresholds | `settings`, `clock`, `db`, `open_context` |
| `unit/types/`, `unit/config/` | fixed point, logging | none |
| `integration/api/` | HTTP contract, roles, persistence | `client`, `auth`, `db`, `helpers.py`, `portfolio_setup.py` |
| `integration/repository/` | migration runner | `conn` |
| `architecture/` | structural invariants (NFR-08) | `app`, `db` |
| `e2e/` | browser journeys (opt-in `-m e2e`) | see `e2e/CLAUDE.md` |

## Conventions
- Tag AC tests with `@pytest.mark.ac("AC-NN")` and start the docstring with `AC-NN.n:`. `--strict-markers` is on, and `test_ac_traceability.py` fails on missing or unknown ACs.
- Each test gets a fresh temp SQLite DB and seed, with the clock fixed at **2026-09-30** (`conftest.py`).
- Send money as strings in requests. Add one negative case with a JSON number.
- Close every connection you open (`db` fixture). Unclosed connections raise `ResourceWarning` under coverage (KD-03).
- Commit new tests red before the implementation (see `docs/tdd.md`).

# src/service/ — use cases

- Every public function takes a `ServiceContext` (`conn`, `settings`, `clock`) first.
- **One transaction per use case.** Wrap writes in `with transaction(ctx.conn):`. It is re-entrant: nested calls join the outer transaction, which is how the seed and the NAV refresh stay atomic.
- **Audit.** Every state change a user or advisor makes calls `ctx.audit(...)`. `details` hold IDs, codes and flags only, never names, notes or amounts (NFR-03).
- **Logging.** Use constant event names (`log.info("goal_created", extra={"goal_id": ...})`). The `pii-log-check` hook rejects f-string messages and PII keys.
- **Views.** Services return wire-ready dicts with decimals as strings (`to_wire`). Controllers do not reformat numbers.
- **Time.** Read time only from `ctx.clock` (`today()` for business dates, `now_iso()` for timestamps).
- Do not import `fastapi` or `sqlite3`. Go through repositories.

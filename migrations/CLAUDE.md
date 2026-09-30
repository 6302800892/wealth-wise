# migrations/ — append-only SQL (NFR-05)

- File names follow `NNNN_snake_case.sql`, strictly increasing. They are applied in order by `src/repository/migrations.py`, which records a SHA-256 per file.
- **Never edit or delete a committed file.** Startup fails on a checksum mismatch. The `migration-append-only-check` hook blocks the edit, and CI's `migrations-append-only` job rejects `M`/`D`/`R` in the MR diff. Put corrections in a new file.
- Every append-only table gets `BEFORE UPDATE` and `BEFORE DELETE` triggers with `RAISE(ABORT, 'append-only table: <name>')`, and is added to `tests/architecture/test_append_only_tables.py`.
- **Policy seeds** (rule sets, templates) are migrations too. Insert a template as `DRAFT`, then its rows, then publish. Rows must sum to 10 000 bp per (version, band, horizon) and list every active asset class. The `allocation-sum-invariant-check` hook verifies the sums.
- Store money as `*_paise`, percentages as `*_bp`, and units or NAV as `*_scaled` (×10 000) integers.

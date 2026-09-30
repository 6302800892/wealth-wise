# src/repository/ — persistence (the only `sqlite3` user)

- One module per aggregate (`*_repo.py`). Return frozen dataclasses with `Decimal` fields, and convert scaled integers with `from_scaled_int` / `to_scaled_int`.
- **Append-only tables** (spec §12.2) expose `insert_*` and `find/list_*` only. Never add `update_*` or `delete_*` for them. The DB triggers would abort anyway.
- Ordering for "latest" queries: `ORDER BY <timestamp> DESC, rowid DESC`. Timestamps can tie under the fixed test clock.
- Use parameterised SQL only. The single f-string in `audit_repo.list_for_entities` builds `?` placeholders, never values.
- `migrations.py` is the checksum-verified runner. It normalises CRLF, so Windows checkouts match Linux CI.

# tests/e2e/ — Playwright journeys

- Run with `npm --prefix frontend run build && poetry run pytest tests/e2e -m e2e`. The first time on a machine, also run `playwright install chromium`.
- `conftest.py` starts a real server (`python -m src.main`) on a free port with a **fresh DB per module** and business date 2026-09-30. The `ui` fixture is parametrised over `desktop` (1280×800) and `mobile` (375×812).
- Select elements by `data-testid` only (`page.get_by_test_id`). When a journey needs a new hook, add the attribute in the page component.
- **Snapshots.** `check_aria(locator, f"<name>-{ui.viewport_name}")` compares against `snapshots/*.aria.yml`. Baselines are per viewport because the phone layout hides table headers (KD-06). Regenerate deliberately with `UPDATE_SNAPSHOTS=1` and review the diff. `screenshot(ui, name)` writes PNG evidence to `snapshots/screenshots/`.
- Journeys that change global state, such as publishing a template, run on one viewport only and skip the other with a reason.

"""NFR-08 / AC-02: every published template row in the database sums to exactly 100.00 (10 000 bp)."""

import pytest

from src.repository.db import connect


@pytest.mark.ac("AC-02")
def test_every_published_template_row_sums_to_100(app, settings):
    """AC-02.1: DB invariant — each (version, band, horizon) of a published template sums to 10 000 bp."""
    conn = connect(settings.db_path)
    rows = conn.execute(
        "SELECT r.template_version, r.risk_band, r.horizon_bucket, SUM(r.target_bp) AS total, COUNT(*) AS n"
        " FROM allocation_template_rows r JOIN allocation_template_set_versions v ON v.version = r.template_version"
        " WHERE v.status = 'PUBLISHED' GROUP BY r.template_version, r.risk_band, r.horizon_bucket"
    ).fetchall()
    assert len(rows) >= 9
    for row in rows:
        assert row["total"] == 10_000, dict(row)


def test_each_published_version_covers_all_band_horizon_pairs(app, settings):
    conn = connect(settings.db_path)
    counts = conn.execute(
        "SELECT r.template_version, COUNT(DISTINCT r.risk_band || '/' || r.horizon_bucket)"
        " FROM allocation_template_rows r JOIN allocation_template_set_versions v ON v.version = r.template_version"
        " WHERE v.status = 'PUBLISHED' GROUP BY r.template_version"
    ).fetchall()
    assert counts and all(row[1] == 9 for row in counts)

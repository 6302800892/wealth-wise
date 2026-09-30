"""NFR-08 / AC-10.2: published rule sets and templates cannot be mutated, even with raw SQL."""

import pytest

from src.repository.db import connect


@pytest.fixture
def conn(app, settings):
    connection = connect(settings.db_path)
    yield connection
    connection.close()


@pytest.mark.ac("AC-10")
@pytest.mark.parametrize(
    "statement",
    [
        "UPDATE risk_rule_set_versions SET definition_json = '{}' WHERE version = 1",
        "DELETE FROM risk_rule_set_versions WHERE version = 1",
        "UPDATE allocation_template_set_versions SET status = 'DRAFT' WHERE version = 1",
        "DELETE FROM allocation_template_set_versions WHERE version = 1",
        "UPDATE allocation_template_rows SET target_bp = 0 WHERE template_version = 1",
        "DELETE FROM allocation_template_rows WHERE template_version = 1",
        "INSERT INTO allocation_template_rows (template_version, risk_band, horizon_bucket, asset_class_code,"
        " target_bp) VALUES (1, 'MODERATE', 'SHORT', 'EQUITY', 1)",
    ],
)
def test_raw_sql_mutation_of_published_version_is_aborted(conn, statement):
    """AC-10.2: SQLite triggers abort UPDATE/DELETE/INSERT against published versions."""
    with pytest.raises(Exception, match="immutable|UNIQUE"):
        conn.execute(statement)

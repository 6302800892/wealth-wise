"""AC-02: allocation templates must cover every band × horizon and sum to exactly 100.00 (BR-09, BR-22)."""

from decimal import Decimal

import pytest

from src.domain.allocation_template_validator import check_publishable, check_row_ranges, row_total
from src.types.enums import HorizonBucket, RiskBand
from src.types.errors import WealthWiseError
from tests.factories import ASSET_ORDER, template_rows

KEY = (RiskBand.MODERATE, HorizonBucket.MEDIUM)


def _row(*pcts):
    return {code: Decimal(p) for code, p in zip(ASSET_ORDER, pcts, strict=True)}


@pytest.mark.ac("AC-02")
def test_template_v1_has_nine_rows_each_summing_to_100():
    """AC-02.1: 9 rows, every row sums to exactly 100.00."""
    rows = template_rows()
    assert len(rows) == 9
    for row in rows.values():
        assert row_total(row) == Decimal("100.00")
    check_publishable(rows, ASSET_ORDER)


@pytest.mark.ac("AC-02")
@pytest.mark.parametrize("pcts", [("50", "35", "10", "4"), ("50", "35", "10", "5.01")])
def test_row_not_summing_to_100_blocks_publish(pcts):
    """AC-02.2: rows summing to 99.00 or 100.01 fail with ALLOCATION_SUM_INVALID naming the row."""
    rows = template_rows({KEY: _row(*pcts)})
    with pytest.raises(WealthWiseError) as exc:
        check_publishable(rows, ASSET_ORDER)
    assert exc.value.code == "ALLOCATION_SUM_INVALID"
    assert "MODERATE/MEDIUM" in exc.value.message


@pytest.mark.ac("AC-02")
@pytest.mark.parametrize("bad", ["-1.00", "100.01"])
def test_percentage_outside_range_is_invalid(bad):
    """AC-02.3: negative or > 100.00 percentages are rejected with VALIDATION_FAILED."""
    with pytest.raises(WealthWiseError) as exc:
        check_row_ranges({KEY: _row(bad, "0", "0", "0")})
    assert exc.value.code == "VALIDATION_FAILED"


@pytest.mark.ac("AC-02")
def test_missing_band_horizon_row_blocks_publish():
    """AC-02: every band × horizon combination must be present."""
    rows = template_rows()
    del rows[KEY]
    with pytest.raises(WealthWiseError) as exc:
        check_publishable(rows, ASSET_ORDER)
    assert exc.value.code == "ALLOCATION_SUM_INVALID"


@pytest.mark.ac("AC-02")
def test_missing_asset_class_blocks_publish():
    """AC-02: each row must list every active asset class."""
    rows = template_rows({KEY: {"EQUITY": Decimal("50"), "DEBT": Decimal("50")}})
    with pytest.raises(WealthWiseError):
        check_publishable(rows, ASSET_ORDER)


def test_more_than_two_decimals_is_invalid():
    with pytest.raises(WealthWiseError):
        check_row_ranges({KEY: _row("50.001", "35", "10", "4.999")})

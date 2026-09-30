"""BR-09 / BR-22: allocation template validation — ranges on save, full coverage and sum = 100.00 on publish."""

from collections.abc import Mapping, Sequence
from decimal import Decimal

from src.types.enums import HORIZON_ORDER, RISK_BAND_ORDER
from src.types.errors import WealthWiseError
from src.types.fixed_point import HUNDRED, PERCENT_QUANTUM
from src.types.policy import TemplateKey, TemplateRows

ZERO = Decimal("0")


def row_label(key: TemplateKey) -> str:
    return f"{key[0].value}/{key[1].value}"


def row_total(row: Mapping[str, Decimal]) -> Decimal:
    return sum(row.values(), Decimal("0.00")).quantize(PERCENT_QUANTUM)


def check_row_ranges(rows: TemplateRows) -> None:
    """Each percentage must be 0.00–100.00 with at most 2 decimal places (applies to drafts too)."""
    problems = []
    for key, row in rows.items():
        for code, pct in row.items():
            if pct < ZERO or pct > HUNDRED or pct != pct.quantize(PERCENT_QUANTUM):
                problems.append(f"{row_label(key)} {code}: {pct} must be 0.00–100.00 with 2 dp")
    if problems:
        raise WealthWiseError("VALIDATION_FAILED", "; ".join(problems), {"problems": problems})


def _coverage_problems(rows: TemplateRows, asset_codes: Sequence[str]) -> list[str]:
    problems = []
    expected_codes = set(asset_codes)
    for band in RISK_BAND_ORDER:
        for horizon in HORIZON_ORDER:
            row = rows.get((band, horizon))
            if row is None:
                problems.append(f"{band.value}/{horizon.value}: row missing")
            elif set(row) != expected_codes:
                problems.append(f"{band.value}/{horizon.value}: must list exactly {sorted(expected_codes)}")
    return problems


def check_publishable(rows: TemplateRows, asset_codes: Sequence[str]) -> None:
    """A template set may be published only if every band × horizon row is complete and sums to 100.00."""
    check_row_ranges(rows)
    problems = _coverage_problems(rows, asset_codes)
    for key, row in rows.items():
        total = row_total(row)
        if total != HUNDRED:
            problems.append(f"Row {row_label(key)} sums to {total}")
    if problems:
        raise WealthWiseError("ALLOCATION_SUM_INVALID", "; ".join(problems), {"problems": problems})

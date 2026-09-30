"""AC-10: versioning rules — drafts only are editable; rule sets must be publishable (BR-21 – BR-23)."""

import dataclasses

import pytest

from src.domain.version_policy import ensure_draft, validate_asset_class, validate_rule_set
from src.types.enums import RiskBand, VersionStatus
from src.types.errors import WealthWiseError
from src.types.policy import BandRange
from tests.factories import rule_set_v1


@pytest.mark.ac("AC-10")
def test_published_version_is_immutable():
    """AC-10.2: any edit of a PUBLISHED version raises VERSION_IMMUTABLE."""
    with pytest.raises(WealthWiseError) as exc:
        ensure_draft(VersionStatus.PUBLISHED)
    assert exc.value.code == "VERSION_IMMUTABLE"
    ensure_draft(VersionStatus.DRAFT)


@pytest.mark.ac("AC-10")
def test_v1_rule_set_is_publishable():
    """AC-10: the seeded rule set satisfies BR-01 and BR-22."""
    validate_rule_set(rule_set_v1())


@pytest.mark.ac("AC-10")
@pytest.mark.parametrize("bands", [
    (BandRange(RiskBand.CONSERVATIVE, 6, 14), BandRange(RiskBand.MODERATE, 14, 22), BandRange(RiskBand.AGGRESSIVE, 23, 30)),
    (BandRange(RiskBand.CONSERVATIVE, 6, 12), BandRange(RiskBand.MODERATE, 14, 22), BandRange(RiskBand.AGGRESSIVE, 23, 30)),
    (BandRange(RiskBand.CONSERVATIVE, 7, 13), BandRange(RiskBand.MODERATE, 14, 22), BandRange(RiskBand.AGGRESSIVE, 23, 30)),
    (BandRange(RiskBand.CONSERVATIVE, 6, 13), BandRange(RiskBand.MODERATE, 14, 22), BandRange(RiskBand.AGGRESSIVE, 23, 29)),
    (BandRange(RiskBand.CONSERVATIVE, 6, 13), BandRange(RiskBand.CONSERVATIVE, 14, 22), BandRange(RiskBand.AGGRESSIVE, 23, 30)),
])
def test_overlapping_gapped_or_incomplete_bands_are_rejected(bands):
    """AC-10.5: thresholds must be contiguous, non-overlapping, cover [min, max] and use each band once."""
    with pytest.raises(WealthWiseError) as exc:
        validate_rule_set(dataclasses.replace(rule_set_v1(), bands=bands))
    assert exc.value.code == "VALIDATION_FAILED"


@pytest.mark.ac("AC-01")
def test_fewer_than_six_questions_is_rejected():
    """AC-01 / BR-01: a rule set needs at least 6 questions."""
    rules = rule_set_v1()
    with pytest.raises(WealthWiseError):
        validate_rule_set(dataclasses.replace(rules, questions=rules.questions[:5]))


def test_duplicate_option_ids_are_rejected():
    rules = rule_set_v1()
    first = rules.questions[0]
    broken = dataclasses.replace(first, options=(first.options[0], first.options[0]))
    with pytest.raises(WealthWiseError):
        validate_rule_set(dataclasses.replace(rules, questions=(broken, *rules.questions[1:])))


@pytest.mark.parametrize(("code", "name", "order"), [("equity", "Equity", 1), ("EQ", "", 1), ("REIT", "REITs", 0)])
def test_asset_class_validation(code, name, order):
    with pytest.raises(WealthWiseError):
        validate_asset_class(code, name, order)


def test_valid_asset_class():
    assert validate_asset_class("REIT", " Real estate ", 5) == "Real estate"

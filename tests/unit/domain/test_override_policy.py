"""AC-09: advisor override validation (BR-20)."""

import pytest

from src.domain.override_policy import validate_override
from src.types.enums import OverrideReason, RiskBand
from src.types.errors import WealthWiseError


@pytest.mark.ac("AC-09")
def test_valid_override_returns_reason_and_trimmed_note():
    """AC-09.1: a reason code from the enum and a non-blank note are accepted."""
    reason, note = validate_override(RiskBand.MODERATE, RiskBand.CONSERVATIVE, "CHANGE_IN_CIRCUMSTANCES", "  job loss ")
    assert reason is OverrideReason.CHANGE_IN_CIRCUMSTANCES
    assert note == "job loss"


@pytest.mark.ac("AC-09")
@pytest.mark.parametrize(("reason", "note"), [("NOT_A_REASON", "note"), ("ADVISOR_ASSESSMENT", "   "),
                                              ("ADVISOR_ASSESSMENT", ""), ("ADVISOR_ASSESSMENT", "x" * 1001)])
def test_invalid_reason_or_note_is_rejected(reason, note):
    """AC-09.2: unknown reason, blank note or note > 1000 chars → VALIDATION_FAILED."""
    with pytest.raises(WealthWiseError) as exc:
        validate_override(RiskBand.MODERATE, RiskBand.AGGRESSIVE, reason, note)
    assert exc.value.code == "VALIDATION_FAILED"


@pytest.mark.ac("AC-09")
def test_same_band_is_rejected():
    """AC-09.2: new_band equal to the current band → BAND_UNCHANGED."""
    with pytest.raises(WealthWiseError) as exc:
        validate_override(RiskBand.MODERATE, RiskBand.MODERATE, "ADVISOR_ASSESSMENT", "note")
    assert exc.value.code == "BAND_UNCHANGED"


def test_override_allowed_without_prior_band():
    reason, _ = validate_override(None, RiskBand.MODERATE, "CUSTOMER_REQUEST", "requested by phone")
    assert reason is OverrideReason.CUSTOMER_REQUEST


def test_note_of_exactly_1000_characters_is_allowed():
    validate_override(RiskBand.MODERATE, RiskBand.AGGRESSIVE, "ADVISOR_ASSESSMENT", "x" * 1000)

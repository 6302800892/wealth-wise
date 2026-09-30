"""BR-20: an advisor override needs a different band, an enumerated reason and a 1–1000 character note."""

from src.types.enums import OverrideReason, RiskBand
from src.types.errors import WealthWiseError, validation_error

MAX_NOTE_LENGTH = 1000


def validate_override(current_band: RiskBand | None, new_band: RiskBand, reason_code: str,
                      note: str) -> tuple[OverrideReason, str]:
    """Return the parsed reason and the trimmed note, or raise."""
    try:
        reason = OverrideReason(reason_code)
    except ValueError as error:
        raise validation_error("reason_code", f"reason_code must be one of {[r.value for r in OverrideReason]}") \
            from error
    cleaned = note.strip()
    if not cleaned or len(cleaned) > MAX_NOTE_LENGTH:
        raise validation_error("note", f"note must be 1–{MAX_NOTE_LENGTH} characters")
    if current_band is new_band:
        raise WealthWiseError("BAND_UNCHANGED", f"customer is already {new_band.value}")
    return reason, cleaned

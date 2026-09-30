"""BR-01 / BR-21 – BR-23: draft-only editing, publishable rule sets and asset-class master rules."""

import re

from src.types.enums import RISK_BAND_ORDER, VersionStatus
from src.types.errors import WealthWiseError, validation_error
from src.types.policy import RuleSet

MIN_QUESTIONS = 6
MIN_OPTIONS = 2
_ASSET_CODE = re.compile(r"^[A-Z][A-Z0-9_]{1,19}$")


def ensure_draft(status: VersionStatus) -> None:
    if status is not VersionStatus.DRAFT:
        raise WealthWiseError("VERSION_IMMUTABLE", "published versions are immutable; create a new draft instead")


def _question_problems(rule_set: RuleSet) -> list[str]:
    problems = []
    if len(rule_set.questions) < MIN_QUESTIONS:
        problems.append(f"at least {MIN_QUESTIONS} questions are required")
    question_ids = [q.id for q in rule_set.questions]
    if len(set(question_ids)) != len(question_ids):
        problems.append("question ids must be unique")
    for question in rule_set.questions:
        option_ids = [o.id for o in question.options]
        if len(option_ids) < MIN_OPTIONS or len(set(option_ids)) != len(option_ids):
            problems.append(f"{question.id}: needs at least {MIN_OPTIONS} options with unique ids")
        if any(o.score < 0 for o in question.options):
            problems.append(f"{question.id}: option scores must be zero or positive")
    return problems


def _band_problems(rule_set: RuleSet) -> list[str]:
    if not rule_set.questions or any(not q.options for q in rule_set.questions):
        return []
    low = sum(min(o.score for o in q.options) for q in rule_set.questions)
    high = sum(max(o.score for o in q.options) for q in rule_set.questions)
    bands = sorted(rule_set.bands, key=lambda b: b.min_score)
    problems = []
    if sorted(b.band for b in bands) != sorted(RISK_BAND_ORDER):
        problems.append("each risk band must appear exactly once")
    expected_start = low
    for band_range in bands:
        if band_range.min_score != expected_start or band_range.max_score < band_range.min_score:
            problems.append(f"{band_range.band.value}: range must start at {expected_start} with no gap or overlap")
        expected_start = band_range.max_score + 1
    if expected_start != high + 1:
        problems.append(f"bands must end exactly at the maximum score {high}")
    return problems


def validate_rule_set(rule_set: RuleSet) -> None:
    """A publishable rule set has ≥ 6 well-formed questions and contiguous bands covering every score."""
    problems = _question_problems(rule_set) + _band_problems(rule_set)
    if problems:
        raise WealthWiseError("VALIDATION_FAILED", "; ".join(problems), {"problems": problems})


def validate_asset_class(code: str, name: str, display_order: int) -> str:
    if not _ASSET_CODE.match(code):
        raise validation_error("code", "code must be 2–20 upper-case letters, digits or underscores")
    cleaned = name.strip()
    if not cleaned or len(cleaned) > 50:
        raise validation_error("name", "name must be 1–50 characters")
    if display_order < 1:
        raise validation_error("display_order", "display_order must be at least 1")
    return cleaned

"""BR-01 – BR-04: deterministic questionnaire scoring and risk-band lookup."""

from collections.abc import Sequence
from dataclasses import dataclass

from src.types.enums import RiskBand
from src.types.errors import WealthWiseError
from src.types.policy import RuleSet


@dataclass(frozen=True)
class Assessment:
    total_score: int
    risk_band: RiskBand


def score_answers(rule_set: RuleSet, answers: Sequence[tuple[str, str]]) -> int:
    """Sum option scores. Every question must be answered exactly once with one of its own options."""
    questions = {q.id: {o.id: o.score for o in q.options} for q in rule_set.questions}
    problems: list[str] = []
    answered: set[str] = set()
    total = 0
    for question_id, option_id in answers:
        if question_id in answered:
            problems.append(f"{question_id}: answered more than once")
            continue
        answered.add(question_id)
        options = questions.get(question_id)
        if options is None:
            problems.append(f"{question_id}: not part of rule set v{rule_set.version}")
        elif option_id not in options:
            problems.append(f"{question_id}: option {option_id} does not belong to this question")
        else:
            total += options[option_id]
    missing = [q.id for q in rule_set.questions if q.id not in answered]
    if problems or missing:
        raise WealthWiseError(
            "INVALID_ANSWERS", "questionnaire answers are incomplete or invalid",
            {"problems": problems, "missing": missing},
        )
    return total


def band_for_score(rule_set: RuleSet, score: int) -> RiskBand:
    for band_range in rule_set.bands:
        if band_range.min_score <= score <= band_range.max_score:
            return band_range.band
    raise WealthWiseError("INVALID_ANSWERS", f"score {score} is outside every band of rule set v{rule_set.version}")


def assess(rule_set: RuleSet, answers: Sequence[tuple[str, str]]) -> Assessment:
    total = score_answers(rule_set, answers)
    return Assessment(total_score=total, risk_band=band_for_score(rule_set, total))

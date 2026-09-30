"""Test data builders that mirror the spec tables (§8.1, §8.4) independently of the seed migrations."""

from decimal import Decimal

from src.types.enums import HorizonBucket, RiskBand
from src.types.policy import AnswerOption, BandRange, Question, RuleSet, TemplateSet

ASSET_ORDER = ["EQUITY", "DEBT", "GOLD", "CASH"]

TEMPLATE_V1 = {
    (RiskBand.CONSERVATIVE, HorizonBucket.SHORT): (10, 60, 10, 20),
    (RiskBand.CONSERVATIVE, HorizonBucket.MEDIUM): (20, 60, 10, 10),
    (RiskBand.CONSERVATIVE, HorizonBucket.LONG): (30, 55, 10, 5),
    (RiskBand.MODERATE, HorizonBucket.SHORT): (30, 50, 10, 10),
    (RiskBand.MODERATE, HorizonBucket.MEDIUM): (50, 35, 10, 5),
    (RiskBand.MODERATE, HorizonBucket.LONG): (60, 27, 10, 3),
    (RiskBand.AGGRESSIVE, HorizonBucket.SHORT): (45, 40, 10, 5),
    (RiskBand.AGGRESSIVE, HorizonBucket.MEDIUM): (70, 20, 7, 3),
    (RiskBand.AGGRESSIVE, HorizonBucket.LONG): (80, 12, 5, 3),
}


def rule_set_v1(version: int = 1) -> RuleSet:
    questions = tuple(
        Question(
            id=f"Q{q}",
            text=f"Question {q}",
            options=tuple(AnswerOption(id=f"Q{q}_{letter}", text=letter, score=score)
                          for score, letter in enumerate("ABCDE", start=1)),
        )
        for q in range(1, 7)
    )
    bands = (
        BandRange(RiskBand.CONSERVATIVE, 6, 13),
        BandRange(RiskBand.MODERATE, 14, 22),
        BandRange(RiskBand.AGGRESSIVE, 23, 30),
    )
    return RuleSet(version=version, questions=questions, bands=bands)


def answers_for_scores(*scores: int) -> list[tuple[str, str]]:
    """Build (question_id, option_id) pairs whose option scores are `scores`."""
    return [(f"Q{i}", f"Q{i}_{'ABCDE'[s - 1]}") for i, s in enumerate(scores, start=1)]


def template_rows(overrides: dict | None = None) -> dict:
    rows = {
        key: {code: Decimal(pct).quantize(Decimal("0.01")) for code, pct in zip(ASSET_ORDER, pcts, strict=True)}
        for key, pcts in TEMPLATE_V1.items()
    }
    rows.update(overrides or {})
    return rows


def template_set_v1(version: int = 1) -> TemplateSet:
    return TemplateSet(version=version, rows=template_rows())

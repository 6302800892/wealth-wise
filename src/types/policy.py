"""Versioned policy value objects: questionnaire rule sets and allocation template sets."""

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from src.types.enums import HorizonBucket, RiskBand


@dataclass(frozen=True)
class AnswerOption:
    id: str
    text: str
    score: int


@dataclass(frozen=True)
class Question:
    id: str
    text: str
    options: tuple[AnswerOption, ...]


@dataclass(frozen=True)
class BandRange:
    band: RiskBand
    min_score: int
    max_score: int


@dataclass(frozen=True)
class RuleSet:
    version: int
    questions: tuple[Question, ...]
    bands: tuple[BandRange, ...]


TemplateKey = tuple[RiskBand, HorizonBucket]
TemplateRows = Mapping[TemplateKey, Mapping[str, Decimal]]


@dataclass(frozen=True)
class TemplateSet:
    version: int
    rows: TemplateRows


def rule_set_from_definition(version: int, definition: Mapping[str, Any]) -> RuleSet:
    """Build a RuleSet from its stored JSON definition."""
    questions = tuple(
        Question(
            id=q["id"],
            text=q["text"],
            options=tuple(AnswerOption(id=o["id"], text=o["text"], score=int(o["score"])) for o in q["options"]),
        )
        for q in definition["questions"]
    )
    bands = tuple(
        BandRange(band=RiskBand(b["band"]), min_score=int(b["min_score"]), max_score=int(b["max_score"]))
        for b in definition["bands"]
    )
    return RuleSet(version=version, questions=questions, bands=bands)


def rule_set_to_definition(rule_set: RuleSet) -> dict[str, Any]:
    return {
        "questions": [
            {"id": q.id, "text": q.text,
             "options": [{"id": o.id, "text": o.text, "score": o.score} for o in q.options]}
            for q in rule_set.questions
        ],
        "bands": [{"band": b.band.value, "min_score": b.min_score, "max_score": b.max_score} for b in rule_set.bands],
    }

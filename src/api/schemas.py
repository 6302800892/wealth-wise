"""Request schemas. Money, units and percentages are strings (NFR-01); JSON numbers are rejected."""

from datetime import date

from pydantic import BaseModel, ConfigDict, Field

from src.types.enums import GoalPriority, GoalType, OverrideReason, RiskBand


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class AnswerIn(StrictModel):
    question_id: str = Field(min_length=1, max_length=32)
    option_id: str = Field(min_length=1, max_length=32)


class AssessmentRequest(StrictModel):
    rule_set_version: int = Field(ge=1)
    answers: list[AnswerIn] = Field(max_length=100)


class GoalCreateRequest(StrictModel):
    name: str = Field(max_length=200)
    goal_type: GoalType
    target_amount: str = Field(max_length=32)
    target_date: date
    priority: GoalPriority


class GoalUpdateRequest(StrictModel):
    name: str | None = Field(default=None, max_length=200)
    goal_type: GoalType | None = None
    target_amount: str | None = Field(default=None, max_length=32)
    target_date: date | None = None
    priority: GoalPriority | None = None
    archived: bool | None = None


class RecommendationRequest(StrictModel):
    goal_id: str | None = Field(default=None, max_length=64)


class HoldingRequest(StrictModel):
    asset_class_code: str = Field(min_length=1, max_length=32)
    goal_id: str | None = Field(default=None, max_length=64)
    units: str = Field(max_length=32)


class DismissRequest(StrictModel):
    reason: str | None = Field(default=None, max_length=500)


class OverrideRequest(StrictModel):
    new_band: RiskBand
    reason_code: OverrideReason
    note: str = Field(max_length=2000)


class ManualRecommendationRequest(StrictModel):
    note: str = Field(max_length=2000)

"""Goal records shared across layers."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from src.types.enums import GoalPriority, GoalType


@dataclass(frozen=True)
class GoalRef:
    """The minimum a rule needs to rank goals (BR-10)."""

    id: str
    priority: GoalPriority
    target_date: date
    created_at: str


@dataclass(frozen=True)
class Goal:
    id: str
    customer_id: str
    name: str
    goal_type: GoalType
    target_amount: Decimal
    target_date: date
    priority: GoalPriority
    created_at: str
    updated_at: str
    archived_at: str | None

    def ref(self) -> GoalRef:
        return GoalRef(id=self.id, priority=self.priority, target_date=self.target_date, created_at=self.created_at)

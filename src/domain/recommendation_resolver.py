"""BR-10 / BR-11: primary-goal selection, template lookup and deterministic input fingerprints."""

import hashlib
import json
from collections.abc import Sequence
from decimal import Decimal

from src.types.enums import GoalPriority, HorizonBucket, RiskBand
from src.types.errors import WealthWiseError
from src.types.goals import GoalRef
from src.types.policy import TemplateSet

PRIORITY_RANK = {GoalPriority.HIGH: 0, GoalPriority.MEDIUM: 1, GoalPriority.LOW: 2}


def select_primary_goal(goals: Sequence[GoalRef]) -> GoalRef | None:
    """Highest priority, then earliest target date, then earliest created_at, then lowest id."""
    if not goals:
        return None
    return min(goals, key=lambda g: (PRIORITY_RANK[g.priority], g.target_date, g.created_at, g.id))


def resolve_allocation(template: TemplateSet, band: RiskBand, horizon: HorizonBucket) -> dict[str, Decimal]:
    row = template.rows.get((band, horizon))
    if row is None:
        raise WealthWiseError(
            "TEMPLATE_ROW_MISSING", f"template v{template.version} has no row for {band.value}/{horizon.value}"
        )
    return dict(row)


def input_fingerprint(band: RiskBand, horizon: HorizonBucket, template_version: int, goal_id: str) -> str:
    canonical = json.dumps(
        {"risk_band": band.value, "horizon_bucket": horizon.value,
         "template_version": template_version, "goal_id": goal_id},
        sort_keys=True, separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

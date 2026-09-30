"""BR-24: KYC stub gate and recommendation preconditions (AC-04.5)."""

from src.types.enums import RiskBand
from src.types.errors import WealthWiseError


def ensure_kyc_verified(kyc_verified: bool) -> None:
    if not kyc_verified:
        raise WealthWiseError("KYC_NOT_VERIFIED", "KYC verification is required for recommendations and rebalancing")


def ensure_risk_band(band: RiskBand | None) -> RiskBand:
    if band is None:
        raise WealthWiseError("RISK_PROFILE_REQUIRED", "complete the risk-profile questionnaire first")
    return band


def ensure_goal_present(goal_id: str | None) -> str:
    if goal_id is None:
        raise WealthWiseError("GOAL_REQUIRED", "create at least one financial goal first")
    return goal_id

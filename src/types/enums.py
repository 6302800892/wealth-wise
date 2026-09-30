"""Domain enumerations (spec §7.2). Status fields are always enums, never free-form strings."""

from enum import StrEnum


class RiskBand(StrEnum):
    CONSERVATIVE = "CONSERVATIVE"
    MODERATE = "MODERATE"
    AGGRESSIVE = "AGGRESSIVE"


class HorizonBucket(StrEnum):
    SHORT = "SHORT"
    MEDIUM = "MEDIUM"
    LONG = "LONG"


class Role(StrEnum):
    CUSTOMER = "CUSTOMER"
    ADVISOR = "ADVISOR"
    ADMIN = "ADMIN"


class GoalType(StrEnum):
    RETIREMENT = "RETIREMENT"
    EDUCATION = "EDUCATION"
    HOME = "HOME"
    OTHER = "OTHER"


class GoalPriority(StrEnum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class GoalStatus(StrEnum):
    IN_PROGRESS = "IN_PROGRESS"
    ACHIEVED = "ACHIEVED"


class BandSource(StrEnum):
    QUESTIONNAIRE = "QUESTIONNAIRE"
    ADVISOR_OVERRIDE = "ADVISOR_OVERRIDE"


class OverrideReason(StrEnum):
    CHANGE_IN_CIRCUMSTANCES = "CHANGE_IN_CIRCUMSTANCES"
    QUESTIONNAIRE_MISUNDERSTOOD = "QUESTIONNAIRE_MISUNDERSTOOD"
    ADVISOR_ASSESSMENT = "ADVISOR_ASSESSMENT"
    CUSTOMER_REQUEST = "CUSTOMER_REQUEST"


class VersionStatus(StrEnum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"


class TradeAction(StrEnum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class RebalancingStatus(StrEnum):
    OPEN = "OPEN"
    ACCEPTED = "ACCEPTED"
    DISMISSED = "DISMISSED"
    SUPERSEDED = "SUPERSEDED"


class StubOrderStatus(StrEnum):
    STUB_SUBMITTED = "STUB_SUBMITTED"


class DriftStatus(StrEnum):
    OK = "OK"
    NO_HOLDINGS = "NO_HOLDINGS"
    NO_RECOMMENDATION = "NO_RECOMMENDATION"


RISK_BAND_ORDER = (RiskBand.CONSERVATIVE, RiskBand.MODERATE, RiskBand.AGGRESSIVE)
HORIZON_ORDER = (HorizonBucket.SHORT, HorizonBucket.MEDIUM, HorizonBucket.LONG)

"""Injectable clocks. Domain rules never read time directly; services receive dates from a Clock."""

from datetime import UTC, date, datetime, time
from typing import Protocol


class Clock(Protocol):
    def now(self) -> datetime: ...

    def today(self) -> date: ...


class SystemClock:
    def now(self) -> datetime:
        return datetime.now(UTC)

    def today(self) -> date:
        return self.now().date()


class FixedClock:
    """A clock pinned to one business date (tests, demos, E2E runs)."""

    def __init__(self, business_date: date) -> None:
        self._date = business_date

    def now(self) -> datetime:
        return datetime.combine(self._date, time(9, 0), tzinfo=UTC)

    def today(self) -> date:
        return self._date


def clock_for(business_date: str | None) -> Clock:
    if business_date:
        return FixedClock(date.fromisoformat(business_date))
    return SystemClock()


def iso_timestamp(moment: datetime) -> str:
    return moment.astimezone(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")

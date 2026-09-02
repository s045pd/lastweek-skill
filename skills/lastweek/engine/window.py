"""Seven-day window math. The week is the unit, not a shorter month."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone

ISO_WEEK_RE = re.compile(r"^(\d{4})-W(\d{2})$")
SPAN_DAYS = 7


@dataclass(frozen=True)
class Window:
    start: date
    end: date
    kind: str
    label: str

    def contains(self, value: datetime | date) -> bool:
        day = value.date() if isinstance(value, datetime) else value
        return self.start <= day <= self.end

    def day_list(self) -> list[date]:
        days: list[date] = []
        cursor = self.start
        while cursor <= self.end:
            days.append(cursor)
            cursor += timedelta(days=1)
        return days

    def start_ts(self) -> int:
        return int(datetime(self.start.year, self.start.month, self.start.day, tzinfo=timezone.utc).timestamp())

    def end_ts(self) -> int:
        close = datetime(self.end.year, self.end.month, self.end.day, 23, 59, 59, tzinfo=timezone.utc)
        return int(close.timestamp())

    def as_dict(self) -> dict[str, str]:
        return {
            "start": self.start.isoformat(),
            "end": self.end.isoformat(),
            "kind": self.kind,
            "label": self.label,
        }


def parse_as_of(value: str | None, now: datetime | None = None) -> date:
    clock = now or datetime.now(timezone.utc)
    if not value:
        return clock.date()
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"as-of must be YYYY-MM-DD, got {value!r}") from exc


def rolling_window(as_of: date, span_days: int = SPAN_DAYS) -> Window:
    if span_days < 1:
        raise ValueError("span_days must be >= 1")
    start = as_of - timedelta(days=span_days - 1)
    return Window(start=start, end=as_of, kind="rolling", label=f"rolling {span_days}d")


def iso_window(spec: str) -> Window:
    match = ISO_WEEK_RE.match(spec.strip())
    if not match:
        raise ValueError("iso week must look like 2026-W36")
    year = int(match.group(1))
    week = int(match.group(2))
    if week < 1 or week > 53:
        raise ValueError(f"iso week number out of range: {spec}")
    try:
        start = date.fromisocalendar(year, week, 1)
        end = date.fromisocalendar(year, week, 7)
    except ValueError as exc:
        raise ValueError(f"invalid iso week {spec}") from exc
    return Window(start=start, end=end, kind="iso", label=spec.strip())


def monday_window(as_of: date) -> Window:
    start = as_of - timedelta(days=as_of.weekday())
    return Window(start=start, end=as_of, kind="monday", label="since Monday")


def prior_window(window: Window) -> Window:
    shift = timedelta(days=SPAN_DAYS)
    return Window(
        start=window.start - shift,
        end=window.end - shift,
        kind=window.kind,
        label=f"prior of {window.label}",
    )


def resolve_window(
    *,
    kind: str = "rolling",
    as_of: str | None = None,
    iso_week: str | None = None,
    span_days: int = SPAN_DAYS,
    now: datetime | None = None,
) -> Window:
    if iso_week:
        return iso_window(iso_week)
    end = parse_as_of(as_of, now=now)
    if kind == "monday":
        return monday_window(end)
    if kind == "iso":
        year, week, _ = end.isocalendar()
        return iso_window(f"{year}-W{week:02d}")
    if kind == "rolling":
        return rolling_window(end, span_days=span_days)
    raise ValueError(f"unknown window kind {kind!r}")

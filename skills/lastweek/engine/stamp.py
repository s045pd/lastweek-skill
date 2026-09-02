"""Parse the messy timestamps lanes actually return."""

from __future__ import annotations

from datetime import datetime, timezone
from email.utils import parsedate_to_datetime


def parse_stamp(value: object) -> datetime | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if isinstance(value, (int, float)):
        compact = _compact_date(int(value))
        if compact:
            return compact
        ts = float(value)
        if ts > 1e12:
            ts = ts / 1000.0
        return datetime.fromtimestamp(ts, tz=timezone.utc)
    text = str(value).strip()
    if not text:
        return None
    if text.isdigit():
        return parse_stamp(int(text))
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except ValueError:
        pass
    try:
        parsed = parsedate_to_datetime(str(value))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except (TypeError, ValueError, IndexError):
        return None


def _compact_date(value: int) -> datetime | None:
    text = str(value)
    if len(text) != 8:
        return None
    try:
        parsed = datetime.strptime(text, "%Y%m%d")
    except ValueError:
        return None
    if parsed.year < 1990 or parsed.year > 2100:
        return None
    return parsed.replace(tzinfo=timezone.utc)

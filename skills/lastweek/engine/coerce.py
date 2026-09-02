"""Safe coercions for messy API fields."""

from __future__ import annotations


def as_int(value: object, default: int = 0) -> int:
    try:
        return int(float(str(value).strip()))
    except (TypeError, ValueError):
        return default

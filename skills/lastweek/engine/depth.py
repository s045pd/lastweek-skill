"""How many clips each depth asks a lane to keep."""

from __future__ import annotations

LIMITS = {
    "skim": 8,
    "normal": 18,
    "deep": 36,
}


def limit_for(depth: str) -> int:
    return LIMITS.get(depth, LIMITS["normal"])

"""Topic cleanup, compare splitting, and host-supplied hints."""

from __future__ import annotations

import re
from typing import Any

from engine.models import Hints

_STRIP = [
    r"\bwhat(?:'s| is| are)? happening\b",
    r"\bwhat happened\b",
    r"\bin the last week\b",
    r"\blast seven days\b",
    r"\blast 7 days\b",
    r"\bpast seven days\b",
    r"\bpast 7 days\b",
    r"\bthis iso week\b",
    r"\bthis week\b",
    r"\blast week\b",
    r"\bpast week\b",
    r"\bweekly wrap(?:[- ]?up)?\b",
    r"\bmonday standup\b",
]
_STRIP_RE = re.compile("|".join(_STRIP), re.IGNORECASE)
_COMPARE_RE = re.compile(r"\s+(?:vs\.?|versus)\s+", re.IGNORECASE)
_TOKEN_RE = re.compile(r"[a-z0-9]+", re.IGNORECASE)
_STOP = {
    "the",
    "and",
    "for",
    "with",
    "from",
    "that",
    "this",
    "are",
    "was",
    "were",
    "what",
    "about",
}


def clean_topic(raw: str) -> str:
    text = _STRIP_RE.sub(" ", raw or "")
    text = re.sub(r"\s+", " ", text).strip(" -:,")
    return text


def split_compare(topic: str) -> tuple[str, str] | None:
    parts = _COMPARE_RE.split(topic.strip(), maxsplit=1)
    if len(parts) != 2:
        return None
    left, right = clean_topic(parts[0]), clean_topic(parts[1])
    if not left or not right:
        return None
    return left, right


def tokenize(text: str) -> list[str]:
    tokens = [token.lower() for token in _TOKEN_RE.findall(text or "")]
    return [token for token in tokens if len(token) > 2 and token not in _STOP]


def parse_hints(payload: dict[str, Any] | None) -> Hints:
    if payload is None:
        data: dict[str, Any] = {}
    elif isinstance(payload, dict):
        data = payload
    else:
        raise ValueError("hints JSON must be an object")

    def as_list(value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        return []

    user = data.get("github_user")
    return Hints(
        subreddits=as_list(data.get("subreddits")),
        github_user=str(user).strip() if user else None,
        github_repos=as_list(data.get("github_repos")),
        extra_queries=as_list(data.get("extra_queries")),
    )

"""Shared pulse types."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import date, datetime
from typing import Any

from engine.window import Window


def _jsonable(value: Any) -> Any:
    if is_dataclass(value):
        return {key: _jsonable(item) for key, item in asdict(value).items()}
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {key: _jsonable(item) for key, item in value.items()}
    return value


@dataclass
class Hints:
    subreddits: list[str] = field(default_factory=list)
    github_user: str | None = None
    github_repos: list[str] = field(default_factory=list)
    extra_queries: list[str] = field(default_factory=list)


@dataclass
class Clip:
    clip_id: str
    lane: str
    title: str
    url: str
    body: str = ""
    author: str | None = None
    venue: str | None = None
    published_at: datetime | None = None
    engagement: dict[str, float | int] = field(default_factory=dict)
    quotes: list[str] = field(default_factory=list)
    velocity: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return _jsonable(self)


@dataclass
class Theme:
    title: str
    clips: list[Clip]
    lanes: list[str]
    heat: float

    def to_dict(self) -> dict[str, Any]:
        return _jsonable(self)


@dataclass
class DayBucket:
    day: date
    weekday: str
    clips: list[Clip]
    heat: float

    def to_dict(self) -> dict[str, Any]:
        return _jsonable(self)


@dataclass
class LaneReport:
    lane: str
    ok: bool
    message: str
    clips: list[Clip] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return _jsonable(self)


@dataclass
class WowShift:
    current: Clip
    previous: Clip
    ratio: float


@dataclass
class WowReport:
    born: list[Clip]
    faded: list[Clip]
    accelerating: list[WowShift]
    cooling: list[WowShift]
    index: float | None

    def to_dict(self) -> dict[str, Any]:
        return _jsonable(self)


@dataclass
class Pulse:
    topic: str
    window: Window
    clips: list[Clip]
    themes: list[Theme]
    days: list[DayBucket]
    lanes: list[LaneReport]
    shape: str
    generated_at: datetime
    version: str
    wow: WowReport | None = None
    prior_window: Window | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "schema": "lastweek.pulse/v1",
            "topic": self.topic,
            "window": self.window.as_dict(),
            "shape": self.shape,
            "version": self.version,
            "generated_at": self.generated_at.isoformat(),
            "clips": [clip.to_dict() for clip in self.clips],
            "themes": [theme.to_dict() for theme in self.themes],
            "days": [bucket.to_dict() for bucket in self.days],
            "lanes": [lane.to_dict() for lane in self.lanes],
            "wow": self.wow.to_dict() if self.wow else None,
            "prior_window": self.prior_window.as_dict() if self.prior_window else None,
        }
        return payload

"""Velocity: engagement per hour alive, with a recency tilt."""

from __future__ import annotations

from datetime import datetime, timezone

from engine.models import Clip

LANE_WEIGHT = {
    "reddit": 1.0,
    "hn": 1.08,
    "github": 0.9,
    "markets": 1.25,
    "video": 0.85,
    "news": 0.55,
    "web": 0.5,
}

MIN_HOURS = 4.0
WEEK_HOURS = 168.0


def hours_alive(clip: Clip, as_of: datetime) -> float:
    published = clip.published_at
    if published is None:
        return WEEK_HOURS
    if published.tzinfo is None:
        published = published.replace(tzinfo=timezone.utc)
    if as_of.tzinfo is None:
        as_of = as_of.replace(tzinfo=timezone.utc)
    hours = (as_of - published).total_seconds() / 3600.0
    return max(hours, 0.25)


def engagement_mass(clip: Clip) -> float:
    numbers = clip.engagement or {}
    score = float(numbers.get("score", 0) or 0)
    comments = float(numbers.get("comments", 0) or 0)
    views = float(numbers.get("views", 0) or 0)
    likes = float(numbers.get("likes", 0) or 0)
    stars = float(numbers.get("stars", 0) or 0)
    return score + comments * 0.4 + views / 2000.0 + likes * 0.2 + stars * 0.05


def velocity(clip: Clip, as_of: datetime) -> float:
    hours = max(hours_alive(clip, as_of), MIN_HOURS)
    recency = max(0.35, 1.0 - (hours / WEEK_HOURS) * 0.65)
    weight = LANE_WEIGHT.get(clip.lane, 1.0)
    return (engagement_mass(clip) + 1.0) / hours * recency * weight


def rank_clips(clips: list[Clip], as_of: datetime) -> list[Clip]:
    ranked = list(clips)
    for clip in ranked:
        clip.velocity = velocity(clip, as_of)
    ranked.sort(key=lambda item: item.velocity, reverse=True)
    return ranked

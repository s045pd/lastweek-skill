"""Day-by-day heat strip for a window."""

from __future__ import annotations

from datetime import datetime, timezone

from engine.models import Clip, DayBucket
from engine.score import velocity
from engine.window import Window


def build_strip(clips: list[Clip], window: Window, as_of: datetime) -> list[DayBucket]:
    grouped: dict = {day: [] for day in window.day_list()}
    for clip in clips:
        if clip.published_at is None:
            continue
        published = clip.published_at
        if published.tzinfo is None:
            published = published.replace(tzinfo=timezone.utc)
        day = published.astimezone(timezone.utc).date()
        if day in grouped:
            grouped[day].append(clip)
    buckets: list[DayBucket] = []
    for day, day_clips in grouped.items():
        heat = sum(velocity(clip, as_of) for clip in day_clips)
        buckets.append(
            DayBucket(
                day=day,
                weekday=day.strftime("%a"),
                clips=day_clips,
                heat=heat,
            )
        )
    return buckets


def peak_day(strip: list[DayBucket]) -> DayBucket:
    return max(strip, key=lambda bucket: (bucket.heat, len(bucket.clips)))


def quiet_days(strip: list[DayBucket]) -> list:
    return [bucket.day for bucket in strip if not bucket.clips]

"""Week-over-week overlay: born, faded, accelerating, cooling."""

from __future__ import annotations

from datetime import datetime
from difflib import SequenceMatcher

from engine.models import Clip, WowReport, WowShift
from engine.query import tokenize
from engine.score import engagement_mass
from engine.window import Window

TITLE_RATIO = 0.72
ACCEL = 1.25
COOL = 0.8


def _norm(title: str) -> str:
    return " ".join(tokenize(title))


def _paired(left: Clip, right: Clip) -> bool:
    if left.url and right.url and left.url.rstrip("/") == right.url.rstrip("/"):
        return True
    a, b = _norm(left.title), _norm(right.title)
    if not a or not b:
        return False
    return SequenceMatcher(None, a, b).ratio() >= TITLE_RATIO


def compare_weeks(
    current: list[Clip],
    previous: list[Clip],
    window: Window,
    prior: Window,
    as_of: datetime,
) -> WowReport:
    del window, prior, as_of
    used_prior: set[int] = set()
    born: list[Clip] = []
    accelerating: list[WowShift] = []
    cooling: list[WowShift] = []
    for clip in current:
        match_index = next(
            (
                index
                for index, old in enumerate(previous)
                if index not in used_prior and _paired(clip, old)
            ),
            None,
        )
        if match_index is None:
            born.append(clip)
            continue
        used_prior.add(match_index)
        old = previous[match_index]
        current_mass = engagement_mass(clip)
        prior_mass = max(engagement_mass(old), 0.01)
        ratio = current_mass / prior_mass
        shift = WowShift(current=clip, previous=old, ratio=ratio)
        if ratio >= ACCEL:
            accelerating.append(shift)
        elif ratio <= COOL:
            cooling.append(shift)
    faded = [old for index, old in enumerate(previous) if index not in used_prior]
    current_mass = sum(engagement_mass(clip) for clip in current)
    prior_mass = sum(engagement_mass(clip) for clip in previous)
    index = (current_mass / prior_mass) if prior_mass > 0 else None
    return WowReport(
        born=born,
        faded=faded,
        accelerating=accelerating,
        cooling=cooling,
        index=index,
    )

"""Greedy title clustering. Keep it boring and deterministic."""

from __future__ import annotations

from datetime import datetime

from engine.models import Clip, Theme
from engine.query import tokenize
from engine.score import rank_clips

JACCARD_FLOOR = 0.28
MAX_THEMES = 8


def _jaccard(left: list[str], right: list[str]) -> float:
    a, b = set(left), set(right)
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def cluster_themes(clips: list[Clip], as_of: datetime) -> list[Theme]:
    if not clips:
        return []
    ranked = rank_clips(list(clips), as_of)
    groups: list[list[Clip]] = []
    token_sets: list[list[str]] = []
    for clip in ranked:
        tokens = tokenize(clip.title) or tokenize(clip.body)
        placed = False
        for index, existing in enumerate(token_sets):
            if _jaccard(tokens, existing) >= JACCARD_FLOOR:
                groups[index].append(clip)
                token_sets[index] = list(set(existing) | set(tokens))
                placed = True
                break
        if not placed:
            groups.append([clip])
            token_sets.append(tokens)
    themes: list[Theme] = []
    for group in groups[:MAX_THEMES]:
        lead = group[0]
        lanes = []
        for clip in group:
            if clip.lane not in lanes:
                lanes.append(clip.lane)
        themes.append(
            Theme(
                title=lead.title,
                clips=group,
                lanes=lanes,
                heat=sum(clip.velocity for clip in group),
            )
        )
    themes.sort(key=lambda theme: theme.heat, reverse=True)
    return themes

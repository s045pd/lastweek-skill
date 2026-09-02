"""Polymarket public search. Odds, not opinions."""

from __future__ import annotations

import json

from engine.depth import limit_for
from engine.models import Clip, Hints, LaneReport
from engine.net import Fetcher, FetcherError
from engine.stamp import parse_stamp
from engine.window import Window

SEARCH = "https://gamma-api.polymarket.com/public-search"


def collect(topic: str, window: Window, hints: Hints, depth: str, fetcher: Fetcher) -> LaneReport:
    del hints
    limit = limit_for(depth)
    try:
        payload = fetcher.json(SEARCH, params={"q": topic})
    except FetcherError as exc:
        return LaneReport(lane="markets", ok=False, message=str(exc), clips=[])
    events = _events(payload)
    clips: list[Clip] = []
    for event in events:
        clip = _from_event(event, window)
        if clip:
            clips.append(clip)
        if len(clips) >= limit:
            break
    return LaneReport(lane="markets", ok=True, message=f"{len(clips)} markets", clips=clips)


def _events(payload: object) -> list[dict]:
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]
    if isinstance(payload, dict):
        for key in ("events", "results", "data"):
            rows = payload.get(key)
            if isinstance(rows, list):
                return [row for row in rows if isinstance(row, dict)]
    return []


def _from_event(event: dict, window: Window) -> Clip | None:
    published = parse_stamp(event.get("startDate") or event.get("createdAt") or event.get("endDate"))
    if published and not window.contains(published):
        # Keep in-window events; drop clearly dated outsiders. Undated events stay.
        if event.get("startDate") or event.get("createdAt"):
            return None
    markets = event.get("markets") or []
    market = markets[0] if markets else {}
    prices = _prices(market.get("outcomePrices"))
    yes = prices[0] if prices else None
    volume = market.get("volume") or event.get("volume") or 0
    try:
        volume_n = float(volume)
    except (TypeError, ValueError):
        volume_n = 0.0
    slug = event.get("slug") or market.get("slug") or ""
    url = f"https://polymarket.com/event/{slug}" if slug else "https://polymarket.com"
    question = market.get("question") or event.get("title") or "market"
    percent = f"{round(yes * 100)}%" if isinstance(yes, float) else (str(yes) if yes is not None else "n/a")
    body = f"Yes priced at {percent}."
    if volume_n:
        body += f" Volume {volume_n:.0f}."
    return Clip(
        clip_id=f"markets:{slug or question}",
        lane="markets",
        title=str(event.get("title") or question),
        url=url,
        body=body,
        author=None,
        venue="Polymarket",
        published_at=published,
        engagement={"score": int(volume_n / 100) if volume_n else 0},
    )


def _prices(raw: object) -> list[float]:
    if isinstance(raw, list):
        values = raw
    elif isinstance(raw, str):
        try:
            values = json.loads(raw)
        except json.JSONDecodeError:
            return []
    else:
        return []
    out: list[float] = []
    for item in values:
        try:
            out.append(float(item))
        except (TypeError, ValueError):
            continue
    return out

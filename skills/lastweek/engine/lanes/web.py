"""Brave web search when a key is present. Silent skip otherwise."""

from __future__ import annotations

from engine.config import brave_key
from engine.depth import limit_for
from engine.models import Clip, Hints, LaneReport
from engine.net import Fetcher, FetcherError
from engine.stamp import parse_stamp
from engine.window import Window

BRAVE = "https://api.search.brave.com/res/v1/web/search"


def collect(topic: str, window: Window, hints: Hints, depth: str, fetcher: Fetcher) -> LaneReport:
    del hints
    key = brave_key()
    if not key:
        return LaneReport(lane="web", ok=True, message="no BRAVE_API_KEY, skipped", clips=[])
    limit = min(limit_for(depth), 20)
    try:
        payload = fetcher.json(
            BRAVE,
            headers={"Accept": "application/json", "X-Subscription-Token": key},
            params={"q": topic, "count": limit, "freshness": "pw"},
        )
    except FetcherError as exc:
        return LaneReport(lane="web", ok=False, message=str(exc), clips=[])
    results = ((payload.get("web") or {}).get("results")) or []
    clips: list[Clip] = []
    for row in results:
        published = parse_stamp(row.get("page_age") or row.get("age"))
        if published and not window.contains(published):
            continue
        url = str(row.get("url") or "")
        clips.append(
            Clip(
                clip_id=f"web:{url}",
                lane="web",
                title=str(row.get("title") or "").strip(),
                url=url,
                body=str(row.get("description") or "")[:400],
                author=None,
                venue=row.get("profile", {}).get("name") if isinstance(row.get("profile"), dict) else None,
                published_at=published,
                engagement={},
            )
        )
    return LaneReport(lane="web", ok=True, message=f"{len(clips)} pages", clips=clips)

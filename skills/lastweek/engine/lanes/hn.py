"""Hacker News via Algolia. Free, no key."""

from __future__ import annotations

from engine.coerce import as_int
from engine.depth import limit_for
from engine.models import Clip, Hints, LaneReport
from engine.net import Fetcher, FetcherError
from engine.stamp import parse_stamp
from engine.window import Window

SEARCH = "https://hn.algolia.com/api/v1/search"
SEARCH_BY_DATE = "https://hn.algolia.com/api/v1/search_by_date"
ITEM = "https://hn.algolia.com/api/v1/items"


def collect(topic: str, window: Window, hints: Hints, depth: str, fetcher: Fetcher) -> LaneReport:
    limit = limit_for(depth)
    filters = f"created_at_i>={window.start_ts()},created_at_i<={window.end_ts()}"
    hits: list[dict] = []
    errors: list[str] = []
    for endpoint in (SEARCH, SEARCH_BY_DATE):
        try:
            payload = fetcher.json(
                endpoint,
                params={
                    "query": topic,
                    "tags": "story",
                    "hitsPerPage": limit,
                    "numericFilters": filters,
                },
            )
        except FetcherError as exc:
            errors.append(str(exc))
            continue
        hits.extend(payload.get("hits") or [])
    clips: list[Clip] = []
    seen: set[str] = set()
    for hit in hits:
        object_id = str(hit.get("objectID") or "")
        if not object_id or object_id in seen:
            continue
        seen.add(object_id)
        published = parse_stamp(hit.get("created_at_i") or hit.get("created_at"))
        title = str(hit.get("title") or "").strip()
        if published is None or not window.contains(published) or not title:
            continue
        url = hit.get("url") or f"https://news.ycombinator.com/item?id={object_id}"
        clips.append(
            Clip(
                clip_id=f"hn:{object_id}",
                lane="hn",
                title=title,
                url=url,
                body="",
                author=hit.get("author"),
                venue="HN",
                published_at=published,
                engagement={
                    "score": as_int(hit.get("points")),
                    "comments": as_int(hit.get("num_comments")),
                },
            )
        )
    clips = clips[:limit]
    if depth != "skim":
        _comments(fetcher, clips[:3])
    if not clips and errors:
        return LaneReport(lane="hn", ok=False, message="; ".join(errors), clips=[])
    return LaneReport(lane="hn", ok=True, message=f"{len(clips)} stories", clips=clips)


def _comments(fetcher: Fetcher, clips: list[Clip]) -> None:
    for clip in clips:
        object_id = clip.clip_id.split(":", 1)[-1]
        try:
            payload = fetcher.json(f"{ITEM}/{object_id}")
        except FetcherError:
            continue
        quotes = []
        for child in payload.get("children") or []:
            text = _strip_html(str(child.get("text") or ""))
            author = child.get("author") or "anon"
            if text:
                quotes.append(f"{text} — {author}")
            if len(quotes) >= 3:
                break
        if quotes:
            clip.quotes = quotes


def _strip_html(text: str) -> str:
    import html
    import re

    text = html.unescape(text)
    text = re.sub(r"<p>", "\n", text)
    text = re.sub(r"<[^>]+>", "", text)
    return text.strip()

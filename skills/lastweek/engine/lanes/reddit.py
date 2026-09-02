"""Reddit lane: Pullpush first, public RSS as fallback."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from urllib.parse import quote_plus

from engine.depth import limit_for
from engine.models import Clip, Hints, LaneReport
from engine.net import Fetcher, FetcherError
from engine.stamp import parse_stamp
from engine.window import Window

PULLPUSH_SUB = "https://api.pullpush.io/reddit/search/submission/"
PULLPUSH_COM = "https://api.pullpush.io/reddit/search/comment/"
RSS_SEARCH = "https://www.reddit.com/search.rss"
ATOM = "{http://www.w3.org/2005/Atom}"


def collect(topic: str, window: Window, hints: Hints, depth: str, fetcher: Fetcher) -> LaneReport:
    limit = limit_for(depth)
    queries = [topic, *hints.extra_queries]
    clips: list[Clip] = []
    errors: list[str] = []
    try:
        clips.extend(_pullpush(fetcher, queries, hints.subreddits, window, limit))
    except FetcherError as exc:
        errors.append(str(exc))
    if not clips:
        try:
            clips.extend(_rss(fetcher, queries, hints.subreddits, window, limit))
        except FetcherError as extra:
            errors.append(str(extra))
    unique = _dedupe(clips)[:limit]
    _attach_comments(fetcher, unique[: min(5, len(unique))])
    if not unique and errors:
        return LaneReport(lane="reddit", ok=False, message="; ".join(errors), clips=[])
    return LaneReport(lane="reddit", ok=True, message=f"{len(unique)} threads", clips=unique)


def _pullpush(
    fetcher: Fetcher,
    queries: list[str],
    subreddits: list[str],
    window: Window,
    limit: int,
) -> list[Clip]:
    clips: list[Clip] = []
    targets = [None, *subreddits] if subreddits else [None]
    for query in queries:
        for sub in targets:
            params = {
                "q": query,
                "since": window.start_ts(),
                "until": window.end_ts(),
                "size": limit,
                "sort": "desc",
            }
            if sub:
                params["subreddit"] = sub
            payload = fetcher.json(PULLPUSH_SUB, params=params)
            rows = _rows(payload)
            for row in rows:
                clip = _from_submission(row, window)
                if clip:
                    clips.append(clip)
    return clips


def _rss(
    fetcher: Fetcher,
    queries: list[str],
    subreddits: list[str],
    window: Window,
    limit: int,
) -> list[Clip]:
    clips: list[Clip] = []
    urls = [f"{RSS_SEARCH}?q={quote_plus(query)}&sort=new&t=week" for query in queries]
    for sub in subreddits:
        for query in queries:
            urls.append(
                f"https://www.reddit.com/r/{quote_plus(sub)}/search.rss?q={quote_plus(query)}&restrict_sr=on&sort=new&t=week"
            )
    for url in urls[:6]:
        xml = fetcher.text(url)
        clips.extend(_parse_atom(xml, window, limit))
    return clips


def _parse_atom(xml: str, window: Window, limit: int) -> list[Clip]:
    clips: list[Clip] = []
    try:
        root = ET.fromstring(xml)
    except ET.ParseError:
        return []
    for entry in root.findall(f"{ATOM}entry")[:limit]:
        title = (entry.findtext(f"{ATOM}title") or "").strip()
        href = ""
        link = entry.find(f"{ATOM}link")
        if link is not None:
            href = link.attrib.get("href", "")
        published = parse_stamp(entry.findtext(f"{ATOM}updated") or entry.findtext(f"{ATOM}published"))
        if not title or not published or not window.contains(published):
            continue
        author = entry.findtext(f"{ATOM}author/{ATOM}name")
        venue = None
        category = entry.find(f"{ATOM}category")
        if category is not None:
            venue = category.attrib.get("term") or category.attrib.get("label")
        clips.append(
            Clip(
                clip_id=f"reddit:{href}",
                lane="reddit",
                title=title,
                url=href,
                body=(entry.findtext(f"{ATOM}content") or "")[:500],
                author=f"u/{author}" if author and not str(author).startswith("u/") else author,
                venue=f"r/{venue}" if venue and not str(venue).startswith("r/") else venue,
                published_at=published,
                engagement={},
            )
        )
    return clips


def _from_submission(row: dict, window: Window) -> Clip | None:
    published = parse_stamp(row.get("created_utc") or row.get("created"))
    if published is None or not window.contains(published):
        return None
    title = str(row.get("title") or "").strip()
    if not title:
        return None
    post_id = str(row.get("id") or "")
    permalink = row.get("permalink") or ""
    url = row.get("url") or ""
    if permalink and permalink.startswith("/"):
        url = "https://www.reddit.com" + permalink
    sub = row.get("subreddit") or ""
    author = row.get("author") or ""
    return Clip(
        clip_id=f"reddit:{post_id}",
        lane="reddit",
        title=title,
        url=url,
        body=str(row.get("selftext") or "")[:800],
        author=f"u/{author}" if author else None,
        venue=f"r/{sub}" if sub else None,
        published_at=published,
        engagement={
            "score": int(row.get("score") or 0),
            "comments": int(row.get("num_comments") or 0),
        },
    )


def _attach_comments(fetcher: Fetcher, clips: list[Clip]) -> None:
    for clip in clips:
        post_id = clip.clip_id.split(":", 1)[-1]
        if not post_id:
            continue
        try:
            payload = fetcher.json(PULLPUSH_COM, params={"link_id": post_id, "size": 5, "sort": "desc"})
        except FetcherError:
            continue
        quotes = []
        for row in _rows(payload):
            body = str(row.get("body") or "").strip()
            author = row.get("author") or "unknown"
            if body:
                quotes.append(f"{body} — u/{author}")
        if quotes:
            clip.quotes = quotes[:3]


def _rows(payload: object) -> list[dict]:
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]
    if isinstance(payload, dict):
        data = payload.get("data") or payload.get("children") or []
        rows = []
        for item in data:
            if isinstance(item, dict) and "data" in item and isinstance(item["data"], dict):
                rows.append(item["data"])
            elif isinstance(item, dict):
                rows.append(item)
        return rows
    return []


def _dedupe(clips: list[Clip]) -> list[Clip]:
    seen: set[str] = set()
    unique: list[Clip] = []
    for clip in clips:
        key = clip.url or clip.clip_id
        if key in seen:
            continue
        seen.add(key)
        unique.append(clip)
    return unique

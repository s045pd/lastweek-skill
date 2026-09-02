"""Google News RSS. Editorial layer for the same seven days."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from urllib.parse import quote_plus

from engine.depth import limit_for
from engine.models import Clip, Hints, LaneReport
from engine.net import Fetcher, FetcherError
from engine.stamp import parse_stamp
from engine.window import Window

NEWS = "https://news.google.com/rss/search"


def collect(topic: str, window: Window, hints: Hints, depth: str, fetcher: Fetcher) -> LaneReport:
    del hints
    limit = limit_for(depth)
    query = topic
    today = datetime.now(timezone.utc).date()
    if window.end == today:
        query = f"{topic} when:7d"
    url = f"{NEWS}?q={quote_plus(query)}&hl=en-US&gl=US&ceid=US:en"
    try:
        xml = fetcher.text(url)
    except FetcherError as exc:
        return LaneReport(lane="news", ok=False, message=str(exc), clips=[])
    clips = _parse(xml, window)[:limit]
    return LaneReport(lane="news", ok=True, message=f"{len(clips)} headlines", clips=clips)


def _parse(xml: str, window: Window) -> list[Clip]:
    try:
        root = ET.fromstring(xml)
    except ET.ParseError:
        return []
    clips: list[Clip] = []
    for item in root.findall(".//item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        published = parse_stamp(item.findtext("pubDate"))
        if not title or not link:
            continue
        if published is None or not window.contains(published):
            continue
        clips.append(
            Clip(
                clip_id=f"news:{link}",
                lane="news",
                title=title,
                url=link,
                body=(item.findtext("description") or "")[:400],
                author=item.findtext("source"),
                venue="news",
                published_at=published,
                engagement={},
            )
        )
    return clips

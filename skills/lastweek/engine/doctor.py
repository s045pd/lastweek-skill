"""Cheap per-lane pings. Used by `lastweek doctor`."""

from __future__ import annotations

import shutil

from engine.net import Fetcher, FetcherError, UrlFetcher


def run_doctor(fetcher: Fetcher | None = None) -> dict:
    client = fetcher or UrlFetcher()
    rows = [
        _probe_reddit(client),
        _probe("hn", lambda: client.json("https://hn.algolia.com/api/v1/search", params={"query": "test", "hitsPerPage": 1})),
        _probe("github", lambda: client.json("https://api.github.com/rate_limit")),
        _probe("markets", lambda: client.json("https://gamma-api.polymarket.com/public-search", params={"q": "test"})),
        _probe("news", lambda: client.text("https://news.google.com/rss/search?q=test&hl=en-US&gl=US&ceid=US:en")),
    ]
    ytdlp = shutil.which("yt-dlp")
    rows.append(
        {
            "lane": "video",
            "ok": True,
            "message": f"yt-dlp at {ytdlp}" if ytdlp else "optional: yt-dlp not on PATH",
        }
    )
    return {"ok": all(row["ok"] for row in rows if row["lane"] != "video"), "lanes": rows}


def _probe_reddit(client: Fetcher) -> dict:
    try:
        client.json(
            "https://api.pullpush.io/reddit/search/submission/",
            params={"q": "test", "size": 1},
        )
        return {"lane": "reddit", "ok": True, "message": "reachable"}
    except FetcherError as pullpush_error:
        try:
            client.text("https://www.reddit.com/search.rss?q=test&sort=new&t=week")
            return {
                "lane": "reddit",
                "ok": True,
                "message": f"rss fallback ({pullpush_error})",
            }
        except FetcherError as rss_error:
            return {"lane": "reddit", "ok": False, "message": f"{pullpush_error}; {rss_error}"}


def _probe(lane: str, call) -> dict:
    try:
        call()
        return {"lane": lane, "ok": True, "message": "reachable"}
    except FetcherError as exc:
        return {"lane": lane, "ok": False, "message": str(exc)}
    except Exception as exc:  # noqa: BLE001
        return {"lane": lane, "ok": False, "message": str(exc)}

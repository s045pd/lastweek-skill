"""Lane registry. Each lane is a collect(topic, window, hints, depth, fetcher)."""

from __future__ import annotations

from engine.lanes import github, hn, markets, news, reddit, video, web

DEFAULT_LANES = ["reddit", "hn", "github", "markets", "news"]

REGISTRY = {
    "reddit": reddit.collect,
    "hn": hn.collect,
    "github": github.collect,
    "markets": markets.collect,
    "news": news.collect,
    "video": video.collect,
    "web": web.collect,
}

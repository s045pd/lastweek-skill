from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from engine.models import Clip, Hints
from engine.net import FetcherError
from engine.window import Window, rolling_window


ROOT = Path(__file__).resolve().parents[1]
AS_OF = datetime(2026, 9, 2, 18, 0, tzinfo=timezone.utc)


@pytest.fixture
def as_of() -> datetime:
    return AS_OF


@pytest.fixture
def week() -> Window:
    return rolling_window(AS_OF.date())


@pytest.fixture
def hints() -> Hints:
    return Hints()


def make_clip(
    *,
    clip_id: str = "c1",
    lane: str = "reddit",
    title: str = "People are shipping weekly briefs",
    url: str = "https://example.com/c1",
    body: str = "A lively thread about weekly briefs.",
    author: str | None = "u/demo",
    venue: str | None = "r/MachineLearning",
    published: datetime | None = None,
    score: int = 120,
    comments: int = 40,
    quotes: list[str] | None = None,
) -> Clip:
    return Clip(
        clip_id=clip_id,
        lane=lane,
        title=title,
        url=url,
        body=body,
        author=author,
        venue=venue,
        published_at=published or datetime(2026, 8, 31, 12, 0, tzinfo=timezone.utc),
        engagement={"score": score, "comments": comments},
        quotes=quotes or ["this is the real signal"],
    )


class MapFetcher:
    """URL-prefix stub used by lane tests. No network."""

    def __init__(self, mapping: dict[str, object] | None = None) -> None:
        self.mapping = mapping or {}
        self.calls: list[str] = []

    def _target(self, url: str, params: dict | None) -> str:
        from engine.net import _join

        return _join(url, params)

    def json(self, url: str, headers: dict[str, str] | None = None, params: dict | None = None):
        target = self._target(url, params)
        self.calls.append(target)
        payload = self._lookup(target)
        if payload is None:
            raise FetcherError(f"no stub for {target}", status_code=404)
        if isinstance(payload, str):
            raise FetcherError("stub is text, not json", status_code=500)
        return payload

    def text(self, url: str, headers: dict[str, str] | None = None, params: dict | None = None) -> str:
        target = self._target(url, params)
        self.calls.append(target)
        payload = self._lookup(target)
        if payload is None:
            raise FetcherError(f"no stub for {target}", status_code=404)
        if not isinstance(payload, str):
            raise FetcherError("stub is json, not text", status_code=500)
        return payload

    def _lookup(self, url: str) -> object | None:
        if url in self.mapping:
            return self.mapping[url]
        best: object | None = None
        best_len = -1
        for prefix, payload in self.mapping.items():
            if url.startswith(prefix) and len(prefix) > best_len:
                best = payload
                best_len = len(prefix)
        return best

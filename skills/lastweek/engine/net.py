"""Tiny stdlib HTTP helper. No third-party client."""

from __future__ import annotations

import gzip
import json
import ssl
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Protocol

from engine import __version__

USER_AGENT = f"lastweek/{__version__} (+https://github.com/s045pd/lastweek-skill)"
DEFAULT_TIMEOUT = 20


class FetcherError(Exception):
    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class Fetcher(Protocol):
    def json(self, url: str, headers: dict[str, str] | None = None, params: dict | None = None) -> Any: ...

    def text(self, url: str, headers: dict[str, str] | None = None, params: dict | None = None) -> str: ...


def _join(url: str, params: dict | None) -> str:
    if not params:
        return url
    clean = {key: value for key, value in params.items() if value is not None}
    query = urllib.parse.urlencode(clean, doseq=True)
    sep = "&" if "?" in url else "?"
    return f"{url}{sep}{query}"


class UrlFetcher:
    def __init__(self, timeout: int = DEFAULT_TIMEOUT) -> None:
        self.timeout = timeout
        self._context = ssl.create_default_context()

    def json(self, url: str, headers: dict[str, str] | None = None, params: dict | None = None) -> Any:
        payload = self.text(url, headers=headers, params=params)
        try:
            return json.loads(payload)
        except json.JSONDecodeError as exc:
            raise FetcherError(f"invalid json from {url}") from exc

    def text(self, url: str, headers: dict[str, str] | None = None, params: dict | None = None) -> str:
        target = _join(url, params)
        request_headers = {"User-Agent": USER_AGENT, "Accept": "*/*", "Accept-Encoding": "gzip"}
        if headers:
            request_headers.update(headers)
        request = urllib.request.Request(target, headers=request_headers)
        try:
            with urllib.request.urlopen(request, timeout=self.timeout, context=self._context) as response:
                raw = response.read()
                if response.headers.get("Content-Encoding") == "gzip" or raw[:2] == b"\x1f\x8b":
                    raw = gzip.decompress(raw)
                return raw.decode("utf-8", errors="replace")
        except urllib.error.HTTPError as exc:
            raise FetcherError(f"HTTP {exc.code} for {target}", status_code=exc.code) from exc
        except urllib.error.URLError as exc:
            raise FetcherError(f"network error for {target}: {exc.reason}") from exc

"""Tiny stdlib HTTP helper. No third-party client."""

from __future__ import annotations

import gzip
import http.client
import json
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Protocol

from engine import __version__

USER_AGENT = f"lastweek/{__version__} (+https://github.com/s045pd/lastweek-skill)"
DEFAULT_TIMEOUT = 20
MAX_BODY = 2_000_000
SECRET_HEADERS = ("Authorization", "X-Subscription-Token")


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


class _SafeRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        previous = urllib.parse.urlparse(req.full_url)
        nxt = urllib.parse.urlparse(newurl)
        if previous.netloc.lower() != nxt.netloc.lower() or nxt.scheme != "https":
            raise FetcherError(f"blocked redirect {previous.netloc} -> {nxt.netloc}")
        new = super().redirect_request(req, fp, code, msg, headers, newurl)
        if new is None:
            return None
        for header in SECRET_HEADERS:
            if header in new.headers:
                del new.headers[header]
        return new


def _opener() -> urllib.request.OpenerDirector:
    return urllib.request.build_opener(_SafeRedirect)


class UrlFetcher:
    def __init__(self, timeout: int = DEFAULT_TIMEOUT) -> None:
        self.timeout = timeout
        self._context = ssl.create_default_context()
        self._opener = _opener()

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
        last_http: urllib.error.HTTPError | None = None
        for attempt in range(4):
            try:
                with self._opener.open(request, timeout=self.timeout) as response:
                    raw = response.read(MAX_BODY + 1)
                    if len(raw) > MAX_BODY:
                        raise FetcherError(f"response too large from {target}")
                    if response.headers.get("Content-Encoding") == "gzip" or raw[:2] == b"\x1f\x8b":
                        raw = gzip.decompress(raw)
                        if len(raw) > MAX_BODY:
                            raise FetcherError(f"decompressed response too large from {target}")
                    return raw.decode("utf-8", errors="replace")
            except FetcherError:
                raise
            except urllib.error.HTTPError as exc:
                last_http = exc
                if exc.code == 429 and attempt < 1:
                    time.sleep(1.0)
                    continue
                raise FetcherError(f"HTTP {exc.code} for {target}", status_code=exc.code) from exc
            except (http.client.IncompleteRead, urllib.error.URLError) as exc:
                if attempt < 2:
                    time.sleep(0.5 * (attempt + 1))
                    continue
                reason = getattr(exc, "reason", exc)
                raise FetcherError(f"network error for {target}: {reason}") from exc
        raise FetcherError(
            f"HTTP {last_http.code if last_http else '?'} for {target}",
            status_code=last_http.code if last_http else None,
        )

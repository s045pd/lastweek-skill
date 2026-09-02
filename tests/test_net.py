import urllib.error

from engine.net import FetcherError, UrlFetcher, _join


def test_join_appends_query():
    assert _join("https://example.com/x", {"q": "a b"}) == "https://example.com/x?q=a+b"
    assert _join("https://example.com/x?p=1", {"q": "2"}) == "https://example.com/x?p=1&q=2"
    assert _join("https://example.com/x", None) == "https://example.com/x"


class _Resp:
    def __init__(self, body: bytes, encoding: str = "") -> None:
        self._body = body
        self.headers = {"Content-Encoding": encoding}

    def read(self, size: int | None = None) -> bytes:
        return self._body if size is None else self._body[:size]

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def test_url_fetcher_json(monkeypatch):
    fetcher = UrlFetcher()
    monkeypatch.setattr(fetcher._opener, "open", lambda *args, **kwargs: _Resp(b'{"ok": true}'))
    assert fetcher.json("https://example.com") == {"ok": True}


def test_url_fetcher_http_error(monkeypatch):
    def boom(*args, **kwargs):
        raise urllib.error.HTTPError("https://example.com", 503, "nope", hdrs=None, fp=None)

    fetcher = UrlFetcher()
    monkeypatch.setattr(fetcher._opener, "open", boom)
    try:
        fetcher.text("https://example.com")
        assert False, "expected FetcherError"
    except FetcherError as exc:
        assert exc.status_code == 503

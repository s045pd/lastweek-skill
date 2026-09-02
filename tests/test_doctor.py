from engine.doctor import run_doctor
from engine.net import FetcherError
from tests.conftest import MapFetcher


def test_doctor_reports_ok_and_fail_lanes():
    fetcher = MapFetcher(
        {
            "https://hn.algolia.com/api/v1/search": {"hits": [{"objectID": "1"}]},
            "https://api.pullpush.io/reddit/search/submission/": {"data": []},
            "https://api.github.com/rate_limit": {"rate": {"remaining": 50}},
            "https://gamma-api.polymarket.com/public-search": {"events": []},
            "https://news.google.com/rss/search": "<rss></rss>",
        }
    )
    report = run_doctor(fetcher)
    names = {row["lane"]: row["ok"] for row in report["lanes"]}
    assert names["hn"] is True
    assert names["reddit"] is True
    assert names["github"] is True
    assert names["markets"] is True
    assert names["news"] is True


def test_doctor_marks_failed_lane():
    class Boom(MapFetcher):
        def json(self, url, headers=None, params=None):
            raise FetcherError("down", status_code=503)

        def text(self, url, headers=None, params=None):
            raise FetcherError("down", status_code=503)

    report = run_doctor(Boom())
    assert any(not row["ok"] for row in report["lanes"])

from engine.lanes import video, web
from engine.models import Hints
from engine.window import rolling_window
from tests.conftest import AS_OF, MapFetcher


def test_video_skips_without_binary(monkeypatch):
    monkeypatch.setattr("engine.lanes.video.shutil.which", lambda _: None)
    report = video.collect("topic", rolling_window(AS_OF.date()), Hints(), "skim", None)
    assert report.ok
    assert report.clips == []
    assert "yt-dlp" in report.message


def test_web_skips_without_key(monkeypatch):
    monkeypatch.setattr("engine.lanes.web.brave_key", lambda: None)
    report = web.collect("topic", rolling_window(AS_OF.date()), Hints(), "skim", MapFetcher())
    assert report.ok
    assert report.clips == []


def test_web_parses_brave_rows(monkeypatch):
    monkeypatch.setattr("engine.lanes.web.brave_key", lambda: "secret")
    fetcher = MapFetcher(
        {
            "https://api.search.brave.com/res/v1/web/search": {
                "web": {
                    "results": [
                        {
                            "title": "Weekly pulse tools",
                            "url": "https://example.com/pulse",
                            "description": "hello",
                            "page_age": "2026-08-31T00:00:00Z",
                        }
                    ]
                }
            }
        }
    )
    report = web.collect("pulse", rolling_window(AS_OF.date()), Hints(), "skim", fetcher)
    assert report.ok
    assert report.clips[0].title == "Weekly pulse tools"

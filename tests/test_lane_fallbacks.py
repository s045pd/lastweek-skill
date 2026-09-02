from datetime import datetime, timezone

from engine.lanes import reddit, video
from engine.models import Hints
from engine.net import FetcherError
from engine.window import rolling_window
from tests.conftest import AS_OF, MapFetcher


class FailThenRss(MapFetcher):
    def json(self, url, headers=None, params=None):
        raise FetcherError("pullpush down", status_code=503)


def test_reddit_falls_back_to_rss():
    week = rolling_window(AS_OF.date())
    rss = """<?xml version="1.0"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <title>RSS weekly brief</title>
    <link href="https://www.reddit.com/r/MachineLearning/comments/zz/x/"/>
    <updated>2026-08-31T12:00:00Z</updated>
    <author><name>demo</name></author>
    <category term="MachineLearning"/>
    <content>hello from rss</content>
  </entry>
</feed>"""
    fetcher = FailThenRss({"https://www.reddit.com/search.rss": rss})
    report = reddit.collect("weekly briefs", week, Hints(), "skim", fetcher)
    assert report.ok
    assert report.clips
    assert "RSS weekly brief" in report.clips[0].title


def test_video_collect_parses_ytdlp_json(monkeypatch):
    week = rolling_window(AS_OF.date())
    monkeypatch.setattr("engine.lanes.video.shutil.which", lambda _: "/usr/bin/yt-dlp")

    class Completed:
        stdout = '{"id":"abc","title":"Weekly recap","webpage_url":"https://youtu.be/abc","upload_date":"20260831","view_count":9}\n'

    monkeypatch.setattr("engine.lanes.video.subprocess.run", lambda *a, **k: Completed())
    report = video.collect("recap", week, Hints(), "skim", None)
    assert report.ok
    assert report.clips[0].clip_id == "video:abc"


def test_video_from_row_keeps_in_window_upload():
    week = rolling_window(AS_OF.date())
    clip = video._from_row(
        {
            "id": "abc",
            "title": "Weekly recap",
            "webpage_url": "https://youtu.be/abc",
            "upload_date": "20260831",
            "uploader": "chan",
            "channel": "chan",
            "description": "hello",
            "view_count": 1000,
            "like_count": 10,
            "comment_count": 2,
        },
        week,
    )
    assert clip is not None
    assert clip.lane == "video"
    assert clip.published_at == datetime(2026, 8, 31, tzinfo=timezone.utc)

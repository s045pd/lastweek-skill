from engine.query import is_scan
from engine.lanes import github, hn, news, reddit
from engine.models import Hints
from engine.window import rolling_window
from tests.conftest import AS_OF, MapFetcher


def test_is_scan_when_no_topic_or_now_or_flag():
    assert is_scan([], "", scan_flag=False) is True
    assert is_scan(["now"], "now", scan_flag=False) is True
    assert is_scan(["OpenClaw"], "OpenClaw", scan_flag=False) is False
    assert is_scan(["OpenClaw"], "OpenClaw", scan_flag=True) is True
    assert is_scan(["this week"], "", scan_flag=False) is True


def test_hn_scan_hits_front_page():
    week = rolling_window(AS_OF.date())
    fetcher = MapFetcher(
        {
            "https://hn.algolia.com/api/v1/search?": {
                "hits": [
                    {
                        "objectID": "1",
                        "title": "Front page story",
                        "url": "https://example.com",
                        "author": "pg",
                        "points": 400,
                        "num_comments": 80,
                        "created_at_i": int(AS_OF.timestamp()) - 3600,
                    }
                ]
            },
            "https://hn.algolia.com/api/v1/search_by_date": {"hits": []},
        }
    )
    report = hn.collect("", week, Hints(), "skim", fetcher)
    assert report.ok
    assert report.clips[0].title == "Front page story"
    joined = " ".join(fetcher.calls)
    assert "front_page" in joined or "tags=front_page" in joined or "front_page" in joined.replace("%2C", ",")


def test_news_scan_uses_homepage_rss():
    week = rolling_window(AS_OF.date())
    rss = """<?xml version="1.0"?><rss version="2.0"><channel>
    <item>
      <title>A world headline</title>
      <link>https://news.example/a</link>
      <pubDate>Mon, 31 Aug 2026 12:00:00 GMT</pubDate>
    </item>
    </channel></rss>"""
    fetcher = MapFetcher({"https://news.google.com/rss?": rss})
    report = news.collect("", week, Hints(), "skim", fetcher)
    assert report.ok
    assert report.clips[0].title == "A world headline"
    assert fetcher.calls
    assert all("rss/search" not in url for url in fetcher.calls)


def test_reddit_scan_uses_all_top():
    week = rolling_window(AS_OF.date())
    atom = """<?xml version="1.0"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <title>Hot without a keyword</title>
    <link href="https://www.reddit.com/r/news/comments/zz/x/"/>
    <updated>2026-08-31T12:00:00Z</updated>
    <author><name>demo</name></author>
    <category term="news"/>
    <content>front</content>
  </entry>
</feed>"""
    fetcher = MapFetcher({"https://www.reddit.com/r/all/top.rss": atom})
    report = reddit.collect("", week, Hints(), "skim", fetcher)
    assert report.ok
    assert "Hot without a keyword" in report.clips[0].title
    assert any("/r/all/top.rss" in url for url in fetcher.calls)

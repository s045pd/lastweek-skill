from datetime import datetime, timezone

from engine.lanes import github, hn, markets, news, reddit
from engine.models import Hints
from engine.window import rolling_window
from tests.conftest import AS_OF, MapFetcher

AUG31 = int(datetime(2026, 8, 31, 12, 0, tzinfo=timezone.utc).timestamp())


def test_reddit_parses_pullpush_submissions(week=None):
    week = rolling_window(AS_OF.date())
    fetcher = MapFetcher(
        {
            "https://api.pullpush.io/reddit/search/submission/": {
                "data": [
                    {
                        "id": "abc123",
                        "title": "Weekly brief tools",
                        "selftext": "I want a 7 day window",
                        "author": "demo",
                        "subreddit": "MachineLearning",
                        "url": "https://www.reddit.com/r/MachineLearning/comments/abc123/x/",
                        "permalink": "/r/MachineLearning/comments/abc123/x/",
                        "score": 88,
                        "num_comments": 12,
                        "created_utc": AUG31,
                    }
                ]
            },
            "https://api.pullpush.io/reddit/search/comment/": {
                "data": [
                    {
                        "id": "c1",
                        "author": "wit",
                        "body": "velocity beats volume",
                        "score": 40,
                    }
                ]
            },
        }
    )
    report = reddit.collect("weekly briefs", week, Hints(), "normal", fetcher)
    assert report.ok
    assert report.clips
    clip = report.clips[0]
    assert clip.lane == "reddit"
    assert clip.author == "u/demo"
    assert any("velocity" in q for q in clip.quotes)


def test_hn_parses_algolia_hits():
    week = rolling_window(AS_OF.date())
    fetcher = MapFetcher(
        {
            "https://hn.algolia.com/api/v1/search?": {
                "hits": [
                    {
                        "objectID": "999",
                        "title": "Show HN: lastweek",
                        "url": "https://example.com",
                        "author": "pg",
                        "points": 210,
                        "num_comments": 44,
                        "created_at_i": AUG31,
                    }
                ]
            },
            "https://hn.algolia.com/api/v1/search_by_date": {"hits": []},
            "https://hn.algolia.com/api/v1/items/999": {
                "id": 999,
                "children": [
                    {"id": 1, "author": "dang", "text": "Please keep it civil.", "points": 12, "children": []}
                ],
            },
        }
    )
    report = hn.collect("lastweek", week, Hints(), "normal", fetcher)
    assert report.ok
    assert report.clips[0].venue == "HN"
    assert report.clips[0].engagement["score"] == 210


def test_github_issues_and_repos():
    week = rolling_window(AS_OF.date())
    fetcher = MapFetcher(
        {
            "https://api.github.com/search/issues": {
                "items": [
                    {
                        "id": 1,
                        "title": "Crash on empty window",
                        "html_url": "https://github.com/acme/app/issues/1",
                        "body": "repro included",
                        "user": {"login": "alice"},
                        "comments": 3,
                        "created_at": "2026-08-30T10:00:00Z",
                        "repository_url": "https://api.github.com/repos/acme/app",
                    }
                ]
            },
            "https://api.github.com/search/repositories": {
                "items": [
                    {
                        "id": 2,
                        "full_name": "acme/app",
                        "html_url": "https://github.com/acme/app",
                        "description": "demo",
                        "stargazers_count": 42,
                        "pushed_at": "2026-09-01T10:00:00Z",
                        "owner": {"login": "acme"},
                    }
                ]
            },
        }
    )
    report = github.collect("acme app", week, Hints(), "skim", fetcher)
    assert report.ok
    lanes_titles = {c.title for c in report.clips}
    assert "Crash on empty window" in lanes_titles
    assert any("acme/app" in c.title for c in report.clips)


def test_markets_reads_gamma_search():
    week = rolling_window(AS_OF.date())
    fetcher = MapFetcher(
        {
            "https://gamma-api.polymarket.com/public-search": {
                "events": [
                    {
                        "title": "Will Nvidia beat earnings?",
                        "slug": "nvidia-earnings",
                        "startDate": "2026-08-28T00:00:00Z",
                        "markets": [
                            {
                                "question": "Will Nvidia beat earnings?",
                                "outcomePrices": "[\"0.62\", \"0.38\"]",
                                "volume": "12000",
                            }
                        ],
                    }
                ]
            }
        }
    )
    report = markets.collect("Nvidia", week, Hints(), "skim", fetcher)
    assert report.ok
    assert report.clips[0].lane == "markets"
    assert "62%" in report.clips[0].body or "0.62" in report.clips[0].body


def test_news_parses_rss():
    week = rolling_window(AS_OF.date())
    rss = """<?xml version="1.0"?>
<rss version="2.0"><channel>
<item>
  <title>Nvidia rallies after earnings</title>
  <link>https://news.example/n1</link>
  <pubDate>Mon, 31 Aug 2026 12:00:00 GMT</pubDate>
  <description>Shares jumped.</description>
</item>
</channel></rss>"""
    fetcher = MapFetcher({"https://news.google.com/rss/search": rss})
    report = news.collect("Nvidia", week, Hints(), "skim", fetcher)
    assert report.ok
    assert report.clips[0].title.startswith("Nvidia rallies")

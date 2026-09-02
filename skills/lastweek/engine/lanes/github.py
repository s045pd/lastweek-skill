"""GitHub issues and recently pushed repos."""

from __future__ import annotations

from engine.config import github_token
from engine.coerce import as_int
from engine.depth import limit_for
from engine.models import Clip, Hints, LaneReport
from engine.net import Fetcher, FetcherError
from engine.stamp import parse_stamp
from engine.query import is_blank_topic
from engine.window import Window

ISSUES = "https://api.github.com/search/issues"
REPOS = "https://api.github.com/search/repositories"


def collect(topic: str, window: Window, hints: Hints, depth: str, fetcher: Fetcher) -> LaneReport:
    limit = limit_for(depth)
    token = github_token()
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    span = f"{window.start.isoformat()}..{window.end.isoformat()}"
    clips: list[Clip] = []
    errors: list[str] = []
    if is_blank_topic(topic):
        issue_queries = [f"is:issue created:{span}"]
    else:
        issue_queries = [f"{topic} created:{span}"]
    if hints.github_user:
        issue_queries.append(f"author:{hints.github_user} created:{span}")
    for repo in hints.github_repos:
        issue_queries.append(f"repo:{repo} created:{span}")
    for query in issue_queries:
        try:
            payload = fetcher.json(
                ISSUES,
                headers=headers,
                params={"q": query, "per_page": min(limit, 30), "sort": "created"},
            )
        except FetcherError as exc:
            errors.append(str(exc))
            continue
        for item in payload.get("items") or []:
            clip = _issue(item, window)
            if clip:
                clips.append(clip)
    if is_blank_topic(topic):
        repo_queries = [f"is:public stars:>20 pushed:{span}"]
    else:
        repo_queries = [f"{topic} pushed:{span}"]
    if hints.github_user:
        repo_queries.append(f"user:{hints.github_user} pushed:{span}")
    for query in repo_queries:
        try:
            payload = fetcher.json(
                REPOS,
                headers=headers,
                params={"q": query, "per_page": min(limit, 20), "sort": "updated"},
            )
        except FetcherError as exc:
            errors.append(str(exc))
            continue
        for item in payload.get("items") or []:
            clip = _repo(item, window)
            if clip:
                clips.append(clip)
    unique = _dedupe(clips)[:limit]
    if not unique and errors:
        return LaneReport(lane="github", ok=False, message="; ".join(errors), clips=[])
    return LaneReport(lane="github", ok=True, message=f"{len(unique)} items", clips=unique)


def _issue(item: dict, window: Window) -> Clip | None:
    published = parse_stamp(item.get("created_at"))
    if published is None or not window.contains(published):
        return None
    repo = ""
    repo_url = str(item.get("repository_url") or "")
    if "/repos/" in repo_url:
        repo = repo_url.split("/repos/", 1)[1]
    user = (item.get("user") or {}).get("login")
    return Clip(
        clip_id=f"github:issue:{item.get('id')}",
        lane="github",
        title=str(item.get("title") or "").strip(),
        url=str(item.get("html_url") or ""),
        body=str(item.get("body") or "")[:500],
        author=user,
        venue=repo or None,
        published_at=published,
        engagement={"comments": as_int(item.get("comments"))},
    )


def _repo(item: dict, window: Window) -> Clip | None:
    published = parse_stamp(item.get("pushed_at") or item.get("updated_at"))
    if published is None or not window.contains(published):
        return None
    name = str(item.get("full_name") or item.get("name") or "")
    return Clip(
        clip_id=f"github:repo:{item.get('id')}",
        lane="github",
        title=f"{name} pushed",
        url=str(item.get("html_url") or ""),
        body=str(item.get("description") or ""),
        author=(item.get("owner") or {}).get("login"),
        venue=name or None,
        published_at=published,
        engagement={"stars": as_int(item.get("stargazers_count"))},
    )


def _dedupe(clips: list[Clip]) -> list[Clip]:
    seen: set[str] = set()
    unique: list[Clip] = []
    for clip in clips:
        if clip.url in seen:
            continue
        seen.add(clip.url)
        unique.append(clip)
    return unique

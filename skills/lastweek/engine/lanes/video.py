"""YouTube via yt-dlp when the binary is present."""

from __future__ import annotations

import json
import shutil
import subprocess

from engine.depth import limit_for
from engine.models import Clip, Hints, LaneReport
from engine.stamp import parse_stamp
from engine.query import is_blank_topic
from engine.window import Window


def collect(topic: str, window: Window, hints: Hints, depth: str, fetcher) -> LaneReport:
    del hints, fetcher
    if is_blank_topic(topic):
        return LaneReport(lane="video", ok=True, message="scan skips video", clips=[])
    binary = shutil.which("yt-dlp")
    if not binary:
        return LaneReport(lane="video", ok=True, message="yt-dlp not on PATH, skipped", clips=[])
    limit = min(limit_for(depth), 12)
    after = window.start.strftime("%Y%m%d")
    command = [
        binary,
        f"ytsearch{limit}:{topic}",
        "--skip-download",
        "--dump-json",
        "--no-warnings",
        "--playlist-end",
        str(limit),
        "--dateafter",
        after,
        "--datebefore",
        window.end.strftime("%Y%m%d"),
    ]
    try:
        completed = subprocess.run(command, capture_output=True, text=True, timeout=60, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return LaneReport(lane="video", ok=False, message=str(exc), clips=[])
    clips: list[Clip] = []
    for line in completed.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        clip = _from_row(row, window)
        if clip:
            clips.append(clip)
    if completed.returncode != 0 and not clips:
        err = (completed.stderr or completed.stdout or "yt-dlp failed").strip().splitlines()
        return LaneReport(lane="video", ok=False, message=err[0][:200] if err else "yt-dlp failed", clips=[])
    return LaneReport(lane="video", ok=True, message=f"{len(clips)} videos", clips=clips)


def _from_row(row: dict, window: Window) -> Clip | None:
    published = parse_stamp(row.get("upload_date") or row.get("timestamp") or row.get("release_timestamp"))
    if row.get("upload_date") and isinstance(row.get("upload_date"), str) and len(row["upload_date"]) == 8:
        raw = row["upload_date"]
        published = parse_stamp(f"{raw[0:4]}-{raw[4:6]}-{raw[6:8]}")
    if published is None or not window.contains(published):
        return None
    video_id = str(row.get("id") or "")
    url = row.get("webpage_url") or (f"https://www.youtube.com/watch?v={video_id}" if video_id else "")
    return Clip(
        clip_id=f"video:{video_id or url}",
        lane="video",
        title=str(row.get("title") or "").strip(),
        url=url,
        body=str(row.get("description") or "")[:400],
        author=row.get("uploader") or row.get("channel"),
        venue=row.get("channel"),
        published_at=published,
        engagement={
            "views": int(row.get("view_count") or 0),
            "likes": int(row.get("like_count") or 0),
            "comments": int(row.get("comment_count") or 0),
        },
    )

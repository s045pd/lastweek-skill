"""Fan out across lanes, then score, cluster, and optionally overlay last week."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from typing import Callable

from engine import __version__
from engine.cluster import cluster_themes
from engine.lanes import DEFAULT_LANES, REGISTRY
from engine.models import Clip, Hints, LaneReport, Pulse
from engine.net import UrlFetcher
from engine.score import rank_clips
from engine.timeline import build_strip
from engine.window import Window, prior_window
from engine.wow import compare_weeks

CollectFn = Callable[..., LaneReport]


def run_pulse(
    topic: str,
    *,
    window: Window,
    hints: Hints | None = None,
    depth: str = "normal",
    shape: str = "pulse",
    wow: bool = False,
    lanes: dict[str, CollectFn] | None = None,
    fetcher=None,
    as_of: datetime | None = None,
    version: str = __version__,
) -> Pulse:
    hints = hints or Hints()
    as_of = as_of or datetime.now(timezone.utc)
    fetcher = fetcher or UrlFetcher()
    collectors = lanes or {name: REGISTRY[name] for name in DEFAULT_LANES}
    reports = _fanout(topic, window, hints, depth, collectors, fetcher)
    clips = _merge(reports, window)
    clips = rank_clips(clips, as_of)
    wow_report = None
    previous = None
    if wow:
        previous = prior_window(window)
        prior_reports = _fanout(topic, previous, hints, depth, collectors, fetcher)
        prior_clips = _merge(prior_reports, previous)
        wow_report = compare_weeks(clips, prior_clips, window, previous, as_of)
    return Pulse(
        topic=topic,
        window=window,
        clips=clips,
        themes=cluster_themes(clips, as_of),
        days=build_strip(clips, window, as_of),
        lanes=reports,
        shape=shape,
        generated_at=as_of,
        version=version,
        wow=wow_report,
        prior_window=previous,
    )


def _fanout(
    topic: str,
    window: Window,
    hints: Hints,
    depth: str,
    collectors: dict[str, CollectFn],
    fetcher,
) -> list[LaneReport]:
    reports: list[LaneReport] = []
    if not collectors:
        return reports
    with ThreadPoolExecutor(max_workers=min(8, len(collectors))) as pool:
        futures = {
            pool.submit(collect, topic, window, hints, depth, fetcher): name
            for name, collect in collectors.items()
        }
        for future in as_completed(futures):
            name = futures[future]
            try:
                reports.append(future.result())
            except Exception as exc:  # noqa: BLE001 - lane isolation
                reports.append(LaneReport(lane=name, ok=False, message=str(exc), clips=[]))
    order = {name: index for index, name in enumerate(collectors)}
    reports.sort(key=lambda report: order.get(report.lane, 99))
    return reports


def _merge(reports: list[LaneReport], window: Window) -> list[Clip]:
    clips: list[Clip] = []
    seen: set[str] = set()
    for report in reports:
        for clip in report.clips:
            if clip.published_at and not window.contains(clip.published_at):
                continue
            key = clip.url or clip.clip_id
            if key in seen:
                continue
            seen.add(key)
            clips.append(clip)
    return clips

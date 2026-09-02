from datetime import datetime, timezone

from engine.models import Hints, LaneReport
from engine.pulse import run_pulse
from engine.window import rolling_window
from tests.conftest import make_clip


AS_OF = datetime(2026, 9, 2, 18, 0, tzinfo=timezone.utc)


def _lane(name: str, clips):
    def collect(topic, window, hints, depth, fetcher):
        return LaneReport(lane=name, ok=True, message="stub", clips=clips)

    return collect


def test_run_pulse_merges_lanes_and_builds_strip():
    clips_a = [make_clip(clip_id="r1", title="OpenClaw memory", url="https://reddit.com/r1")]
    clips_b = [make_clip(clip_id="h1", lane="hn", title="OpenClaw on HN", url="https://news.ycombinator.com/item?id=1", score=70)]
    pulse = run_pulse(
        "OpenClaw",
        window=rolling_window(AS_OF.date()),
        hints=Hints(),
        depth="normal",
        shape="pulse",
        wow=False,
        lanes={
            "reddit": _lane("reddit", clips_a),
            "hn": _lane("hn", clips_b),
        },
        fetcher=object(),
        as_of=AS_OF,
        version="0.1.0",
    )
    assert {c.clip_id for c in pulse.clips} == {"r1", "h1"}
    assert pulse.themes
    assert len(pulse.days) == 7
    assert pulse.wow is None


def test_run_pulse_wow_fills_prior_via_second_collect():
    calls = []

    def collect(topic, window, hints, depth, fetcher):
        calls.append(window.start.isoformat())
        if window.end.isoformat() <= "2026-08-26":
            clips = [make_clip(clip_id="old", title="Old rumor", score=20)]
        else:
            clips = [make_clip(clip_id="new", title="Fresh leak", score=90)]
        return LaneReport(lane="reddit", ok=True, message="stub", clips=clips)

    pulse = run_pulse(
        "Nvidia",
        window=rolling_window(AS_OF.date()),
        hints=Hints(),
        depth="normal",
        shape="pulse",
        wow=True,
        lanes={"reddit": collect},
        fetcher=object(),
        as_of=AS_OF,
        version="0.1.0",
    )
    assert pulse.wow is not None
    assert pulse.wow.born
    assert len(calls) == 2


def test_run_pulse_isolates_lane_exceptions():
    def boom(*args, **kwargs):
        raise RuntimeError("lane exploded")

    pulse = run_pulse(
        "x",
        window=rolling_window(AS_OF.date()),
        hints=Hints(),
        depth="skim",
        shape="pulse",
        wow=False,
        lanes={"reddit": boom},
        fetcher=object(),
        as_of=AS_OF,
        version="0.1.0",
    )
    assert pulse.clips == []
    assert pulse.lanes[0].ok is False
    assert "exploded" in pulse.lanes[0].message

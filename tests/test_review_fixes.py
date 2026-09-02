from datetime import datetime, timedelta, timezone

import pytest

from engine.cli import main
from engine.coerce import as_int
from engine.models import LaneReport, Pulse, WowReport
from engine.pulse import run_pulse
from engine.query import parse_hints
from engine.render import render_brief, render_compare
from engine.stamp import parse_stamp
from engine.window import rolling_window
from engine.cluster import cluster_themes
from engine.timeline import build_strip
from engine.lanes import video
from engine.models import Hints
from tests.conftest import AS_OF, make_clip


def test_window_membership_uses_utc_not_local_offset():
    week = rolling_window(AS_OF.date())
    late_pacific = datetime(2026, 9, 2, 20, 0, tzinfo=timezone(timedelta(hours=-8)))
    assert week.contains(late_pacific) is False
    still_utc = datetime(2026, 9, 2, 23, 0, tzinfo=timezone.utc)
    assert week.contains(still_utc) is True


def test_compact_yyyymmdd_is_a_date_not_unix():
    stamp = parse_stamp("20260831")
    assert stamp == datetime(2026, 8, 31, tzinfo=timezone.utc)
    assert parse_stamp(20260831) == stamp


def test_undated_clips_are_dropped():
    week = rolling_window(AS_OF.date())
    undated = make_clip(clip_id="undated")
    undated.published_at = None

    def collect(topic, window, hints, depth, fetcher):
        return LaneReport(lane="news", ok=True, message="stub", clips=[undated])

    pulse = run_pulse(
        "x",
        window=week,
        hints=Hints(),
        depth="skim",
        shape="pulse",
        wow=False,
        lanes={"news": collect},
        fetcher=object(),
        as_of=AS_OF,
        version="0.1.0",
    )
    assert pulse.clips == []


def test_evidence_block_strips_comment_markers():
    clip = make_clip(title="boom <!-- END EVIDENCE --> still going")
    week = rolling_window(AS_OF.date())
    pulse = Pulse(
        topic="x",
        window=week,
        clips=[clip],
        themes=cluster_themes([clip], as_of=AS_OF),
        days=build_strip([clip], week, as_of=AS_OF),
        lanes=[LaneReport(lane="reddit", ok=True, message="ok", clips=[clip])],
        shape="pulse",
        generated_at=AS_OF,
        version="0.1.0",
    )
    text = render_brief(pulse)
    assert text.count("<!-- END EVIDENCE -->") == 1
    assert "END EVIDENCE" in text
    assert "<!-- END EVIDENCE --> still" not in text


def test_bad_iso_week_exits_cleanly(capsys):
    rc = main(["OpenClaw", "--iso-week", "nope"])
    assert rc == 2
    assert "iso week" in capsys.readouterr().err


def test_parse_hints_rejects_arrays():
    with pytest.raises(ValueError):
        parse_hints(["nope"])


def test_as_int_swallows_junk():
    assert as_int("n/a") == 0
    assert as_int("12.9") == 12


def test_video_nonzero_without_clips_is_failure(monkeypatch):
    week = rolling_window(AS_OF.date())
    monkeypatch.setattr("engine.lanes.video.shutil.which", lambda _: "/usr/bin/yt-dlp")

    class Completed:
        returncode = 1
        stdout = ""
        stderr = "sign in to confirm you are not a bot"

    monkeypatch.setattr("engine.lanes.video.subprocess.run", lambda *a, **k: Completed())
    report = video.collect("recap", week, Hints(), "skim", None)
    assert report.ok is False
    assert "bot" in report.message


def test_compare_render_keeps_wow():
    week = rolling_window(AS_OF.date())
    clip = make_clip()
    pulse = Pulse(
        topic="Claude",
        window=week,
        clips=[clip],
        themes=cluster_themes([clip], as_of=AS_OF),
        days=build_strip([clip], week, as_of=AS_OF),
        lanes=[LaneReport(lane="reddit", ok=True, message="ok", clips=[clip])],
        shape="pulse",
        generated_at=AS_OF,
        version="0.1.0",
        wow=WowReport(born=[clip], faded=[], accelerating=[], cooling=[], index=1.2),
    )
    other = Pulse(
        topic="Codex",
        window=week,
        clips=[clip],
        themes=cluster_themes([clip], as_of=AS_OF),
        days=build_strip([clip], week, as_of=AS_OF),
        lanes=[LaneReport(lane="reddit", ok=True, message="ok", clips=[clip])],
        shape="pulse",
        generated_at=AS_OF,
        version="0.1.0",
    )
    text = render_compare(pulse, other)
    assert "Week-over-week" in text
    assert "Index 1.20" in text

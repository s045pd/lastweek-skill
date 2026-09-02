from datetime import datetime, timezone

from engine.models import LaneReport, Pulse
from engine.render import render_brief, render_compare
from engine.window import rolling_window
from tests.conftest import make_clip


AS_OF = datetime(2026, 9, 2, 18, 0, tzinfo=timezone.utc)


def _pulse(shape: str = "pulse") -> Pulse:
    week = rolling_window(AS_OF.date())
    clip = make_clip(quotes=["the weekly cadence is the point"])
    from engine.cluster import cluster_themes
    from engine.timeline import build_strip

    clips = [clip]
    return Pulse(
        topic="weekly briefs",
        window=week,
        clips=clips,
        themes=cluster_themes(clips, as_of=AS_OF),
        days=build_strip(clips, week, as_of=AS_OF),
        lanes=[LaneReport(lane="reddit", ok=True, message="ok", clips=clips)],
        shape=shape,
        generated_at=AS_OF,
        version="0.1.0",
    )


def test_brief_stamp_and_coverage_markers():
    text = render_brief(_pulse())
    assert text.splitlines()[0].startswith("⏱ lastweek 0.1.0")
    assert "2026-08-27 → 2026-09-02" in text
    assert "This week's pulse: weekly briefs" in text
    assert "<!-- COVERAGE -->" in text
    assert "<!-- END COVERAGE -->" in text
    assert "<!-- EVIDENCE" in text
    assert "reddit" in text


def test_brief_avoids_last30days_voice():
    text = render_brief(_pulse())
    forbidden = [
        "What I learned",
        "All agents reported back",
        "KEY PATTERNS",
        "last30days",
        "LAW 1",
    ]
    for phrase in forbidden:
        assert phrase not in text


def test_wrap_and_standup_labels():
    assert "Week wrap: weekly briefs" in render_brief(_pulse("wrap"))
    assert "Since Monday: weekly briefs" in render_brief(_pulse("standup"))


def test_compare_render_names_both_sides():
    left = _pulse()
    left.topic = "Claude"
    right = _pulse()
    right.topic = "Codex"
    text = render_compare(left, right)
    assert "Compare: Claude vs Codex this week." in text
    assert "<!-- COVERAGE -->" in text

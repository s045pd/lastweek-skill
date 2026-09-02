from engine.models import LaneReport, Pulse, WowReport, WowShift
from engine.render import render_brief
from engine.window import prior_window, rolling_window
from engine.cluster import cluster_themes
from engine.timeline import build_strip
from tests.conftest import AS_OF, make_clip


def test_brief_includes_wow_section():
    week = rolling_window(AS_OF.date())
    current = make_clip(title="Nvidia earnings thread", score=400)
    previous = make_clip(title="Nvidia earnings thread", score=40)
    clips = [current]
    pulse = Pulse(
        topic="Nvidia",
        window=week,
        clips=clips,
        themes=cluster_themes(clips, as_of=AS_OF),
        days=build_strip(clips, week, as_of=AS_OF),
        lanes=[LaneReport(lane="reddit", ok=True, message="ok", clips=clips)],
        shape="wrap",
        generated_at=AS_OF,
        version="0.1.0",
        wow=WowReport(
            born=[],
            faded=[],
            accelerating=[WowShift(current=current, previous=previous, ratio=10.0)],
            cooling=[],
            index=2.5,
        ),
        prior_window=prior_window(week),
    )
    text = render_brief(pulse)
    assert "Week wrap: Nvidia" in text
    assert "Week-over-week" in text
    assert "Index 2.50" in text
    assert "↑ Nvidia earnings thread" in text

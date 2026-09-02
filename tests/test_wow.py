from datetime import datetime, timezone

from engine.window import prior_window, rolling_window
from engine.wow import compare_weeks
from tests.conftest import make_clip


AS_OF = datetime(2026, 9, 2, 18, 0, tzinfo=timezone.utc)


def test_wow_detects_new_gone_and_accelerating():
    current = [
        make_clip(
            clip_id="same",
            title="Nvidia earnings thread",
            url="https://reddit.com/r/x/same",
            score=400,
            comments=80,
        ),
        make_clip(
            clip_id="new",
            title="Brand new leak",
            url="https://reddit.com/r/x/new",
            score=50,
        ),
        make_clip(
            clip_id="cooling",
            title="Cooling story",
            url="https://reddit.com/r/x/cool",
            score=10,
        ),
    ]
    previous = [
        make_clip(
            clip_id="same-old",
            title="Nvidia earnings thread",
            url="https://reddit.com/r/x/same",
            score=80,
            comments=10,
        ),
        make_clip(
            clip_id="gone",
            title="Last week's rumor",
            url="https://reddit.com/r/x/gone",
            score=300,
        ),
        make_clip(
            clip_id="cooling-old",
            title="Cooling story",
            url="https://reddit.com/r/x/cool",
            score=200,
        ),
    ]
    week = rolling_window(AS_OF.date())
    report = compare_weeks(current, previous, week, prior_window(week), as_of=AS_OF)
    assert any("leak" in c.title.lower() for c in report.born)
    assert any("rumor" in c.title.lower() for c in report.faded)
    assert report.accelerating
    assert report.cooling
    assert report.index > 0.5


def test_wow_empty_prior_is_all_born():
    current = [make_clip()]
    week = rolling_window(AS_OF.date())
    report = compare_weeks(current, [], week, prior_window(week), as_of=AS_OF)
    assert len(report.born) == 1
    assert report.faded == []
    assert report.index is None

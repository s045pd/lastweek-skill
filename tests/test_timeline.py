from datetime import datetime, timezone

from engine.timeline import build_strip, peak_day, quiet_days
from engine.window import rolling_window
from tests.conftest import make_clip


AS_OF = datetime(2026, 9, 2, 18, 0, tzinfo=timezone.utc)


def test_strip_has_one_bucket_per_window_day():
    week = rolling_window(AS_OF.date())
    clips = [
        make_clip(clip_id="a", published=datetime(2026, 8, 31, 4, 0, tzinfo=timezone.utc), score=40),
        make_clip(clip_id="b", published=datetime(2026, 8, 31, 9, 0, tzinfo=timezone.utc), score=80),
        make_clip(clip_id="c", published=datetime(2026, 9, 2, 1, 0, tzinfo=timezone.utc), score=10),
    ]
    strip = build_strip(clips, week, as_of=AS_OF)
    assert [bucket.day.isoformat() for bucket in strip] == [
        "2026-08-27",
        "2026-08-28",
        "2026-08-29",
        "2026-08-30",
        "2026-08-31",
        "2026-09-01",
        "2026-09-02",
    ]
    monday = next(b for b in strip if b.day.isoformat() == "2026-08-31")
    assert [c.clip_id for c in monday.clips] == ["a", "b"]
    assert monday.heat > 0


def test_peak_and_quiet_days():
    week = rolling_window(AS_OF.date())
    clips = [
        make_clip(clip_id="hot", published=datetime(2026, 9, 1, 12, 0, tzinfo=timezone.utc), score=400),
    ]
    strip = build_strip(clips, week, as_of=AS_OF)
    assert peak_day(strip).day.isoformat() == "2026-09-01"
    quiet = {d.isoformat() for d in quiet_days(strip)}
    assert "2026-09-01" not in quiet
    assert "2026-08-27" in quiet

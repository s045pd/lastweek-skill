from datetime import datetime, timezone

from engine.score import engagement_mass, hours_alive, rank_clips, velocity
from tests.conftest import make_clip


AS_OF = datetime(2026, 9, 2, 18, 0, tzinfo=timezone.utc)


def test_hours_alive_uses_as_of_not_wall_clock():
    clip = make_clip(published=datetime(2026, 9, 1, 18, 0, tzinfo=timezone.utc))
    assert hours_alive(clip, AS_OF) == 24.0


def test_engagement_mass_weights_comments_below_score():
    loud = make_clip(score=100, comments=0)
    chatty = make_clip(score=0, comments=100)
    assert engagement_mass(loud) > engagement_mass(chatty)


def test_velocity_prefers_fresh_over_stale_equal_mass():
    fresh = make_clip(
        clip_id="fresh",
        published=datetime(2026, 9, 2, 12, 0, tzinfo=timezone.utc),
        score=80,
        comments=10,
    )
    stale = make_clip(
        clip_id="stale",
        published=datetime(2026, 8, 27, 12, 0, tzinfo=timezone.utc),
        score=80,
        comments=10,
    )
    assert velocity(fresh, AS_OF) > velocity(stale, AS_OF)


def test_markets_lane_gets_a_quality_bump():
    reddit = make_clip(lane="reddit", score=50, comments=0)
    market = make_clip(lane="markets", score=50, comments=0, url="https://polymarket.com/e")
    assert velocity(market, AS_OF) > velocity(reddit, AS_OF)


def test_rank_clips_orders_by_velocity_desc():
    slow = make_clip(
        clip_id="slow",
        published=datetime(2026, 8, 27, 1, 0, tzinfo=timezone.utc),
        score=10,
    )
    fast = make_clip(
        clip_id="fast",
        published=datetime(2026, 9, 2, 16, 0, tzinfo=timezone.utc),
        score=90,
    )
    ranked = rank_clips([slow, fast], as_of=AS_OF)
    assert [c.clip_id for c in ranked] == ["fast", "slow"]
    assert ranked[0].velocity >= ranked[1].velocity

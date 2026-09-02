from datetime import datetime, timezone

from engine.cluster import cluster_themes
from tests.conftest import make_clip


AS_OF = datetime(2026, 9, 2, 18, 0, tzinfo=timezone.utc)


def test_similar_titles_share_a_theme():
    clips = [
        make_clip(
            clip_id="1",
            title="OpenClaw ships memory fix",
            published=datetime(2026, 9, 2, 10, 0, tzinfo=timezone.utc),
            score=200,
        ),
        make_clip(
            clip_id="2",
            title="OpenClaw memory fix lands",
            lane="hn",
            published=datetime(2026, 9, 2, 11, 0, tzinfo=timezone.utc),
            score=90,
        ),
        make_clip(
            clip_id="3",
            title="Unrelated knitting patterns",
            published=datetime(2026, 8, 28, 11, 0, tzinfo=timezone.utc),
            score=12,
        ),
    ]
    themes = cluster_themes(clips, as_of=AS_OF)
    assert len(themes) >= 2
    lead = themes[0]
    ids = {c.clip_id for c in lead.clips}
    assert "1" in ids
    assert "2" in ids
    assert "3" not in ids
    assert "hn" in lead.lanes
    assert "reddit" in lead.lanes


def test_empty_input_returns_no_themes():
    assert cluster_themes([], as_of=AS_OF) == []

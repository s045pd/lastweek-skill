from engine.cli import main
from engine.cluster import cluster_themes
from engine.models import LaneReport, Pulse
from engine.timeline import build_strip
from engine.window import rolling_window
from tests.conftest import AS_OF, make_clip


def _pulse(topic: str = "weekly briefs") -> Pulse:
    week = rolling_window(AS_OF.date())
    clips = [make_clip()]
    return Pulse(
        topic=topic,
        window=week,
        clips=clips,
        themes=cluster_themes(clips, as_of=AS_OF),
        days=build_strip(clips, week, as_of=AS_OF),
        lanes=[LaneReport(lane="reddit", ok=True, message="ok", clips=clips)],
        shape="pulse",
        generated_at=AS_OF,
        version="0.1.0",
    )


def test_main_prints_brief(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr("engine.cli.run_pulse", lambda *args, **kwargs: _pulse())
    rc = main(["weekly briefs", "--as-of", "2026-09-02", "--save-dir", str(tmp_path)])
    assert rc == 0
    out = capsys.readouterr().out
    assert "PULSE · weekly briefs" in out
    assert "⏱ lastweek" in out
    saved = list(tmp_path.glob("*.md"))
    assert saved


def test_main_compare(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(
        "engine.cli.run_pulse",
        lambda topic, **kwargs: _pulse(topic),
    )
    rc = main(["Claude vs Codex", "--as-of", "2026-09-02", "--save-dir", str(tmp_path)])
    assert rc == 0
    out = capsys.readouterr().out
    assert "COMPARE · Claude vs Codex" in out


def test_main_doctor(monkeypatch, capsys):
    monkeypatch.setattr(
        "engine.cli.run_doctor",
        lambda: {"ok": True, "lanes": [{"lane": "hn", "ok": True, "message": "reachable"}]},
    )
    rc = main(["doctor"])
    assert rc == 0
    assert "hn" in capsys.readouterr().out


def test_main_json_doctor(monkeypatch, capsys):
    monkeypatch.setattr(
        "engine.cli.run_doctor",
        lambda: {"ok": False, "lanes": [{"lane": "hn", "ok": False, "message": "down"}]},
    )
    rc = main(["doctor", "--emit", "json"])
    assert rc == 1
    assert '"ok": false' in capsys.readouterr().out.lower().replace("false", "false")


def test_main_help_when_empty(capsys):
    rc = main([])
    assert rc == 2


def test_main_doctor_who_is_research(monkeypatch, tmp_path):
    seen = {}

    def fake_pulse(topic, **kwargs):
        seen["topic"] = topic
        return _pulse(topic)

    monkeypatch.setattr("engine.cli.run_pulse", fake_pulse)
    rc = main(["Doctor Who", "--as-of", "2026-09-02", "--save-dir", str(tmp_path)])
    assert rc == 0
    assert seen["topic"] == "Doctor Who"

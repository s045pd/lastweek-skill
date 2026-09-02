import json
from pathlib import Path

from engine import __version__


def test_version_matches_plugin_and_skill():
    root = Path(__file__).resolve().parents[1]
    plugin = json.loads((root / ".claude-plugin/plugin.json").read_text(encoding="utf-8"))
    assert plugin["version"] == __version__
    skill = (root / "skills/lastweek/SKILL.md").read_text(encoding="utf-8")
    assert f'version: "{__version__}"' in skill

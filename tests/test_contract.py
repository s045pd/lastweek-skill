from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = (ROOT / "skills/lastweek/SKILL.md").read_text(encoding="utf-8")
README = (ROOT / "README.md").read_text(encoding="utf-8")


def test_skill_frontmatter_identity():
    assert SKILL.startswith("---\n")
    assert "name: lastweek" in SKILL.split("---", 2)[1]


def test_skill_does_not_copy_last30days_contract():
    banned = [
        "What I learned:",
        "All agents reported back",
        "LAW 1",
        "STEP 0.55",
        "STEP 0.75",
        "Peter Steinberger",
        "last30days.py",
        "KEY PATTERNS from the research",
        "ScrapeCreators",
    ]
    for phrase in banned:
        assert phrase not in SKILL, phrase
        assert phrase not in README, phrase


def test_skill_requires_the_engine():
    assert "skills/lastweek/run.py" in SKILL
    assert "PULSE RULES" in SKILL
    assert "--wow" in SKILL
    assert "--iso-week" in SKILL


def test_readme_sells_the_week_not_the_month():
    assert "seven-day" in README.lower() or "seven day" in README.lower() or "7-day" in README.lower()
    assert "/lastweek" in README

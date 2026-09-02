# Contributing

lastweek is a seven-day pulse engine. Patches should make the week sharper,
not turn this into a generic multi-week research suite.

## Setup

```
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -e ".[dev]"
python3 -m pytest
```

## Where to change things

| Job | Place |
|---|---|
| Window math | `skills/lastweek/engine/window.py` |
| Velocity | `skills/lastweek/engine/score.py` |
| A source | `skills/lastweek/engine/lanes/` |
| Brief shape | `skills/lastweek/engine/render.py` and `skills/lastweek/SKILL.md` |
| Agent contract | `skills/lastweek/SKILL.md` |

Keep the engine stdlib-only. If a lane needs a binary (yt-dlp) or a key
(Brave), skip cleanly when it is missing.

## Tests

Add a unit test next to the behavior. Lane tests must use `MapFetcher` - no
live network in CI.

## Skill contract

If you change CLI flags, update `SKILL.md` in the same PR. Hosts read that
file, not this one.

# lastweek

**What moved in the last seven days - ranked by velocity, not by volume.**

`/lastweek` is an agent skill plus a Python engine. It pulls public discussion
from Reddit, Hacker News, GitHub, Polymarket, news RSS, and (when present)
YouTube, then scores each clip by how hard it is moving *right now* inside a
seven-day window.

A monthly recap answers "what was the era about." lastweek answers "what
broke, peaked, or went quiet between last {weekday} and today."

```
python3 skills/lastweek/run.py "OpenClaw"
```

```
⏱ lastweek 0.1.0 · rolling 7d · 2026-08-27 → 2026-09-02

PULSE · OpenClaw

Heat by day
Thu ██░░░░ 2
Fri ████░░ 5
...
```

## Why a week

Seven days is short enough that a spike is still a spike. It is long enough
to see a story form, peak, and cool. The engine is built around that grain:

| Capability | What it is for |
|---|---|
| Rolling 7-day window | Default. Today plus the six days behind it. |
| `--window monday` | Since Monday. Morning standup. |
| `--iso-week 2026-W36` | A named calendar week, Monday-Sunday. |
| `--wow` | Fetch the previous seven days and overlay born / faded / accelerating. |
| Day strip | Heat and clip counts per weekday. Quiet days stay visible. |
| Velocity | Engagement per hour alive, with a recency tilt. Yesterday beats last {weekday}. |
| Shapes | `pulse` (default), `wrap` (sendable recap), `standup` (since Monday). |

Compare two names in one window with `Claude vs Codex`. The engine runs both
sides and prints a compare brief.

## Install

**Any [Agent Skills](https://agentskills.io) host (Claude Code, Codex, Cursor, Gemini CLI, Grok, …):**

```
npx skills add s045pd/lastweek-skill
```

**Claude Code marketplace:**

```
/plugin marketplace add s045pd/lastweek-skill
/plugin install lastweek
```

**From a checkout:**

```
python3 skills/lastweek/run.py "your topic"
```

Python 3.11+. No third-party packages. Reddit, Hacker News, GitHub,
Polymarket, and Google News RSS run with zero keys.

## Optional unlocks

| Want | Set or install |
|---|---|
| Higher GitHub quota | `GITHUB_TOKEN` or `gh auth login` |
| Web lane | `BRAVE_API_KEY` |
| YouTube | `yt-dlp` on PATH |
| Custom dump folder | `LASTWEEK_SAVE_DIR` (default `~/Documents/LastWeek`) |

Copy [.env.example](.env.example) to `~/.config/lastweek/env` if you want a
file instead of a shell profile.

## CLI

```
python3 skills/lastweek/run.py TOPIC [flags]
python3 skills/lastweek/run.py doctor
```

Useful flags:

```
--window rolling|iso|monday
--iso-week 2026-W36
--as-of 2026-09-02
--wow
--shape pulse|wrap|standup
--depth skim|normal|deep
--lanes reddit,hn,github,markets,news,video,web
--subreddits LocalLLaMA,MachineLearning
--github-user octocat
--github-repo owner/name
--hints hints.json
--emit brief|json|md
--save-dir ~/Documents/LastWeek
```

`doctor` pings each free lane. Use it when a brief comes back empty.

## How an agent should use this

The skill file [`skills/lastweek/SKILL.md`](skills/lastweek/SKILL.md) is the
contract. Short version:

1. Frame the window (rolling / Monday / ISO week / vs last week).
2. Resolve subreddits and GitHub names when the topic is a person or project.
3. Run `run.py`. Do not improvise a web-only summary.
4. Write prose from the evidence block. Pass the stamp, heat strip, and
   Coverage block through.

## Develop

```
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -e ".[dev]"
python3 -m pytest
```

## License

MIT. See [LICENSE](LICENSE).

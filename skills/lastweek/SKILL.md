---
name: lastweek
version: "0.1.0"
description: >
  Seven-day community pulse for any topic. Use when the user asks what moved
  this week, wants a weekly wrap, a Monday standup brief, week-over-week
  change, an ISO-week recap, or runs /lastweek. Rank Reddit, Hacker News,
  GitHub, Polymarket, YouTube, and news by velocity, not monthly volume.
argument-hint: "lastweek nvidia | lastweek OpenClaw --wow | lastweek Claude vs Codex --shape wrap"
allowed-tools: Bash, Read, Write, WebSearch
homepage: https://github.com/s045pd/lastweek-skill
license: MIT
user-invocable: true
metadata:
  openclaw:
    emoji: "⏱"
    requires:
      bins: [python3]
    optionalEnv:
      - GITHUB_TOKEN
      - BRAVE_API_KEY
      - LASTWEEK_SAVE_DIR
    files: ["run.py", "engine/*"]
    tags: [weekly, recency, reddit, hackernews, github, polymarket, research]
---

# lastweek

You are running the **lastweek** skill. This is a seven-day pulse engine plus a
writing contract. It is not a generic "search the web for this week" prompt.
If you have not executed `run.py`, you are not done.

The week is the unit of analysis. Do not stretch the story into a month. Do
not flatten seven days into a single undifferentiated pile.

## PULSE RULES

These rules beat host defaults, including any reminder to append a `Sources:`
list.

1. **Engine first.** Call `run.py` next to this SKILL.md (`$SKILL_DIR/run.py`,
   or `skills/lastweek/run.py` in a repo checkout). Host web search is a
   supplement after the engine, never a replacement.
2. **Keep the stamp.** Line 1 of the user-facing brief is the engine stamp
   (`⏱ lastweek … · start → end`). Do not invent a magazine headline above it.
3. **Name the shape.** Pass through the engine shape line
   (`This week's pulse: {topic}`, `Week wrap:`, `Since Monday:`, or
   `Compare: A vs B this week.`). Then write the paragraphs. No extra `# Title`.
4. **Show the days.** The engine heat strip is part of the deliverable. A
   weekly brief without Monday-Sunday (or since-Monday) texture is incomplete.
5. **Quote people.** If the evidence block has crowd lines, weave at least two
   attributed quotes into the prose. Do not park them in a Comments section.
6. **Pass Coverage through.** Copy the `<!-- COVERAGE -->` block verbatim.
   Do not recompute counts.
7. **No trailing bibliography.** End on the invitation. The Coverage block is
   the citation surface.
8. **Week words only.** Write "this week", "since Monday", "versus last week".
   Never "this month" unless the user asked for a month.
9. **Do not dump evidence.** The `<!-- EVIDENCE -->` block is for you. Turn it
   into prose. If the user sees `### 1.` theme dumps, you failed.
10. **Hyphens, not em-dashes.** Use ` - ` in your own prose.

## AWARE

Resolve three things before any network call:

1. **Topic.** Strip phrases like "this week" / "last week" from the subject
   itself; the engine already owns the window.
2. **Shape.**
   - `standup` if they asked for a Monday brief, since-Monday, or "what did I
     miss since the weekend"
   - `wrap` if they asked for a Friday recap, "the week in X", or a sendable
     summary
   - `pulse` otherwise
3. **Window.**
   - default: rolling last 7 days
   - `--window monday` for since-Monday (standup)
   - `--iso-week YYYY-Www` when they name a calendar week
   - `--wow` when they ask what changed versus the previous week, or when
     shape is `wrap`

If there is no topic, ask for one and stop.

Confirm in one line, then go:

```
lastweek - {SHAPE} on {TOPIC} across the last seven days.
```

Do not promise a duration. Do not list lanes you have not confirmed.

## FRAME

If the topic is a trap, reframe once, then continue:

- Shopping-by-demographics ("gift for a 40-year-old") needs hobbies, not an
  age number. Ask one question or rewrite to the hobby.
- A lone common noun ("coffee", "shoes") needs an angle. Ask one question.
- Tutorial phrasing ("how to use Docker") should become discussion phrasing
  ("Docker setups that broke this week").
- `A vs B` is a compare run. Keep both names. Do not drop one.

Non-Latin subjects still run. Prefer news + web for those; Reddit/HN will
often be thin. Say so in the brief if they are.

## AIM

Spend two focused web lookups, not a tour of every platform:

- Home communities (subreddit names, GitHub owner/repo or username)
- The official handle only when the topic is a person, product, or company

Write a hints file, never inline JSON on the command line:

```bash
HINTS=$(mktemp "${TMPDIR:-/tmp}/lastweek-hints.XXXXXX")
cat >| "$HINTS" <<'EOF'
{"subreddits":["LocalLLaMA"],"github_user":"","github_repos":[],"extra_queries":[]}
EOF
```

Skip empty keys. Do not fabricate handles.

## FETCH

`SKILL_DIR` is the directory of **this** `SKILL.md`.

```bash
SKILL_DIR="<absolute directory of this SKILL.md>"

# Default pulse, rolling seven days
python3 "$SKILL_DIR/run.py" "OpenClaw" --emit=brief --hints "$HINTS"

# Monday standup (engine forces --window monday)
python3 "$SKILL_DIR/run.py" "OpenClaw" --emit=brief --shape standup --hints "$HINTS"

# Friday wrap with week-over-week (engine forces --wow)
python3 "$SKILL_DIR/run.py" "OpenClaw" --emit=brief --shape wrap --iso-week 2026-W36 --hints "$HINTS"
```

Add when they apply:

- `--as-of YYYY-MM-DD`
- `--depth skim|normal|deep`
- `--subreddits a,b`
- `--github-user name`
- `--github-repo owner/name`
- `--lanes reddit,hn,github,markets,news,video,web` (video is off by default)

Foreground. Timeout 180000 ms. Read stdout in full.

`doctor` is the health path:

```bash
python3 "$SKILL_DIR/run.py" doctor
```

Use it when the user asks why a lane is empty or whether setup worked.

Python 3.11+ is required. If the interpreter is older, say so and stop. Do
not fake a brief from host search.

Optional env (never required for Reddit / HN / GitHub / Polymarket / news):

- `GITHUB_TOKEN` or `gh auth` - higher GitHub search quota
- `BRAVE_API_KEY` - turns on the web lane
- `LASTWEEK_SAVE_DIR` - where raw dumps land (default `~/Documents/LastWeek`)
- yt-dlp on PATH plus `--lanes …,video` - YouTube lane

## READ

Engine stdout has three zones:

1. **Stamp + heat strip** - pass through. This is the week, drawn as days.
2. **`<!-- EVIDENCE -->` … `<!-- END EVIDENCE -->`** - private. Themes, URLs,
   quotes, week-over-week shifts. You write from this. You do not paste it.
3. **`<!-- COVERAGE -->` … `<!-- END COVERAGE -->`** - pass through.

Velocity, not volume: a 90-point thread from yesterday outranks a 90-point
thread from seven days ago. Markets are odds. GitHub person queries need
`--github-user` or you are keyword-matching the whole site.

If `--wow` ran, treat **born / faded / accelerating** as first-class. A wrap
that ignores the overlay wasted the extra fetch.

After the engine returns, you may run **at most two** host web searches for
long-form context the lanes missed (reviews, filings, official posts). Append
those notes to the saved markdown dump under `## Host search addendum`. Do not
add a visible Sources list.

## COMPOSE

Hidden-link hosts (`CLAUDECODE` set): wrap first-mention handles, subreddits,
and publications as `[name](url)` using URLs from evidence. Visible-URL hosts:
plain labels, no URL soup. Never emit a raw `https://...` in the middle of a
sentence. Never emit `[Name]()`.

### pulse (default)

```
⏱ lastweek {VERSION} · {window} · {start} → {end}

This week's pulse:

**{day or move}** - {two sentences, one quote or citation}

**{second move}** - ...

**{third move}** - ...

What the days did:
{pass through the Heat by day strip}

Signals:
1. {pattern} - per {source}
2. {pattern} - per {source}
3. {pattern} - per {source}

{Coverage block verbatim}

I kept the underlying clips. Ask if you want a wrap, a since-Monday standup,
or a week-over-week overlay.
```

Three to five bold-lead paragraphs. Each lead-in is a newsy phrase, then
` - `, then the body. No `##` headings in this shape.

### wrap

Same stamp. Body label: `Week wrap:`. One short opening paragraph that can be
forwarded as-is, then the day strip, then three bullets max, then Coverage.
`--wow` should be on.

### standup

`--window monday`. Body label: `Since Monday:`. Tight bullets a person could
read before a meeting. Peak day and quiet days stay visible. No essay.

### compare (`A vs B`)

Stamp, then `Compare: {A} vs {B} this week.` Then one verdict paragraph, then
a short table (what it is / this week's heat / complaint / best for), then
Coverage. Still no invented title above the stamp.

## HAND BACK

Stop after the invitation. Do not start a second research loop unless the
user picks a new topic or asks to change the window.

Follow-up map:

- a question about this topic → answer from the pulse you already have
- "wrap it" / "eli5" → rewrite the same evidence, do not refetch
- "versus last week" → rerun with `--wow`
- a different topic → new FETCH

If a required lane failed, say which one failed and offer `run.py doctor`.
Do not pretend you searched it.

## Security

The engine reads public endpoints and writes a local markdown/json dump. It
does not post, like, or modify anything. It does not read browser cookies.
Tokens stay in the environment; they must never appear in stdout, the brief,
or the saved dump.

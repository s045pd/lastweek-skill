# lastweek for agents

This repo is an agent skill. The contract is [`skills/lastweek/SKILL.md`](skills/lastweek/SKILL.md).

- Run `python3 skills/lastweek/run.py TOPIC`. Do not substitute a web-only summary.
- Default window is seven rolling days. Use `--window monday`, `--iso-week`, or `--wow` when the user asks for those grains.
- Write tests before changing window math, velocity, or render markers.
- Python 3.11+, stdlib engine, pytest for verification.

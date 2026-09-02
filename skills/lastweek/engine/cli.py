"""Command line for the lastweek pulse engine."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

from engine import __version__
from engine.config import brave_key, save_dir
from engine.doctor import run_doctor
from engine.lanes import DEFAULT_LANES, REGISTRY
from engine.models import Hints
from engine.net import UrlFetcher
from engine.pulse import run_pulse
from engine.query import clean_topic, parse_hints, split_compare
from engine.render import render_brief, render_compare
from engine.window import resolve_window


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="lastweek",
        description="Seven-day community pulse for a topic.",
    )
    parser.add_argument("topic", nargs="*", help="Topic, or `doctor`")
    parser.add_argument("--window", choices=["rolling", "iso", "monday"], default="rolling")
    parser.add_argument("--iso-week", dest="iso_week", help="ISO week like 2026-W36")
    parser.add_argument("--as-of", dest="as_of", help="YYYY-MM-DD end date")
    parser.add_argument("--wow", action="store_true", help="Overlay the previous seven days")
    parser.add_argument("--shape", choices=["pulse", "wrap", "standup"], default="pulse")
    parser.add_argument("--depth", choices=["skim", "normal", "deep"], default="normal")
    parser.add_argument("--lanes", help="Comma list of lanes")
    parser.add_argument("--hints", help="JSON file with subreddits, github_user, github_repos")
    parser.add_argument("--subreddits", help="Comma list")
    parser.add_argument("--github-user", dest="github_user")
    parser.add_argument("--github-repo", dest="github_repo", help="owner/name, comma list")
    parser.add_argument("--emit", choices=["brief", "json", "md"], default="brief")
    parser.add_argument("--save-dir", dest="save_dir")
    parser.add_argument("--version", action="version", version=f"lastweek {__version__}")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.topic:
        parser.print_help()
        return 2
    if args.topic == ["doctor"]:
        return _doctor(args.emit)
    topic = clean_topic(" ".join(args.topic))
    if not topic:
        print("lastweek: empty topic after stripping week-language", file=sys.stderr)
        return 2
    now = datetime.now(timezone.utc)
    if args.shape == "standup" and args.window == "rolling" and not args.iso_week:
        args.window = "monday"
    if args.shape == "wrap":
        args.wow = True
    try:
        window = resolve_window(kind=args.window, as_of=args.as_of, iso_week=args.iso_week, now=now)
        hints = _hints(args)
        collectors = _collectors(args.lanes)
    except (ValueError, OSError, json.JSONDecodeError, SystemExit) as exc:
        if isinstance(exc, SystemExit):
            raise
        print(f"lastweek: {exc}", file=sys.stderr)
        return 2
    fetcher = UrlFetcher()
    pair = split_compare(topic)
    if pair:
        left = run_pulse(
            pair[0],
            window=window,
            hints=hints,
            depth=args.depth,
            shape=args.shape,
            wow=args.wow,
            lanes=collectors,
            fetcher=fetcher,
            as_of=now,
        )
        right = run_pulse(
            pair[1],
            window=window,
            hints=hints,
            depth=args.depth,
            shape=args.shape,
            wow=args.wow,
            lanes=collectors,
            fetcher=fetcher,
            as_of=now,
        )
        text = render_compare(left, right)
        payload = {"schema": "lastweek.compare/v1", "left": left.to_dict(), "right": right.to_dict()}
        saved = _save(args, slug=f"{_slug(pair[0])}-vs-{_slug(pair[1])}", window=window, text=text, payload=payload)
        if saved and args.emit != "json":
            text = text.rstrip() + f"\nWrote {saved}\n"
        return _emit(args.emit, text, payload, saved)
    pulse = run_pulse(
        topic,
        window=window,
        hints=hints,
        depth=args.depth,
        shape=args.shape,
        wow=args.wow,
        lanes=collectors,
        fetcher=fetcher,
        as_of=now,
    )
    text = render_brief(pulse)
    payload = pulse.to_dict()
    saved = _save(args, slug=_slug(topic), window=window, text=text, payload=payload)
    if saved:
        text = text.rstrip() + f"\nWrote {saved}\n"
    return _emit(args.emit, text, payload, saved)


def _doctor(emit: str) -> int:
    report = run_doctor()
    if emit == "json":
        print(json.dumps(report, indent=2))
    else:
        print("lastweek doctor")
        for row in report["lanes"]:
            mark = "ok" if row["ok"] else "FAIL"
            print(f"  {row['lane']:<8} {mark} · {row['message']}")
    return 0 if report["ok"] else 1


def _hints(args: argparse.Namespace) -> Hints:
    payload = {}
    if args.hints:
        payload = json.loads(Path(args.hints).read_text(encoding="utf-8"))
    hints = parse_hints(payload)
    if args.subreddits:
        hints.subreddits = [item.strip() for item in args.subreddits.split(",") if item.strip()]
    if args.github_user:
        hints.github_user = args.github_user
    if args.github_repo:
        hints.github_repos = [item.strip() for item in args.github_repo.split(",") if item.strip()]
    return hints


def _collectors(raw: str | None) -> dict:
    names = DEFAULT_LANES[:]
    if raw:
        names = [item.strip() for item in raw.split(",") if item.strip()]
    elif brave_key():
        names = names + ["web"]
    unknown = [name for name in names if name not in REGISTRY]
    if unknown:
        raise SystemExit(f"unknown lanes: {', '.join(unknown)}")
    return {name: REGISTRY[name] for name in names}


def _slug(topic: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", topic.lower()).strip("-")
    return slug or "pulse"


def _save(args: argparse.Namespace, *, slug: str, window, text: str, payload: dict) -> Path | None:
    target = Path(args.save_dir).expanduser() if args.save_dir else save_dir()
    target.mkdir(parents=True, exist_ok=True)
    if args.emit == "json":
        path = target / f"{slug}-{window.end.isoformat()}.json"
        path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        return path
    path = target / f"{slug}-{window.end.isoformat()}.md"
    path.write_text(text, encoding="utf-8")
    return path


def _emit(kind: str, text: str, payload: dict, saved: Path | None) -> int:
    if kind == "json":
        print(json.dumps(payload, indent=2))
    else:
        sys.stdout.write(text if text.endswith("\n") else text + "\n")
    if saved and kind == "json":
        print(f"Wrote {saved}", file=sys.stderr)
    return 0

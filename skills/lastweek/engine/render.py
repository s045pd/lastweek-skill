"""Engine-owned brief. The host model synthesizes; this file stamps and covers."""

from __future__ import annotations

from engine.models import DayBucket, Pulse
from engine.timeline import peak_day, quiet_days

EVIDENCE_OPEN = "<!-- EVIDENCE: for the host model. Do not dump this block to the user. -->"
EVIDENCE_CLOSE = "<!-- END EVIDENCE -->"
COVERAGE_OPEN = "<!-- COVERAGE -->"
COVERAGE_CLOSE = "<!-- END COVERAGE -->"

SHAPE_LABEL = {
    "pulse": "PULSE",
    "wrap": "WRAP",
    "standup": "STANDUP",
}


def render_brief(pulse: Pulse) -> str:
    lines = [_stamp(pulse), "", _headline(pulse), "", *_heat_lines(pulse.days), ""]
    lines.extend(_evidence(pulse))
    lines.append("")
    lines.extend(_coverage(pulse))
    return "\n".join(lines).rstrip() + "\n"


def render_compare(left: Pulse, right: Pulse) -> str:
    lines = [
        _stamp(left),
        "",
        f"COMPARE · {_clean(left.topic)} vs {_clean(right.topic)}",
        "",
        f"Heat · {_clean(left.topic)}",
        *_heat_lines(left.days),
        "",
        f"Heat · {_clean(right.topic)}",
        *_heat_lines(right.days),
        "",
        EVIDENCE_OPEN,
        f"## {_clean(left.topic)}",
        *_theme_lines(left)[1:],
        *_wow_lines(left),
        "",
        f"## {_clean(right.topic)}",
        *_theme_lines(right)[1:],
        *_wow_lines(right),
        EVIDENCE_CLOSE,
        "",
        COVERAGE_OPEN,
        f"Coverage · {left.topic}",
        *_lane_lines(left),
        f"Coverage · {right.topic}",
        *_lane_lines(right),
        COVERAGE_CLOSE,
    ]
    return "\n".join(lines).rstrip() + "\n"


def _stamp(pulse: Pulse) -> str:
    window = pulse.window
    return (
        f"⏱ lastweek {pulse.version} · {window.label} · "
        f"{window.start.isoformat()} → {window.end.isoformat()}"
    )


def _clean(text: str) -> str:
    cleaned = str(text or "").replace("<!--", "").replace("-->", "")
    return " ".join(cleaned.split())


def _headline(pulse: Pulse) -> str:
    label = SHAPE_LABEL.get(pulse.shape, pulse.shape.upper())
    return f"{label} · {_clean(pulse.topic)}"


def _heat_lines(strip: list[DayBucket]) -> list[str]:
    if not strip:
        return ["Heat by day", "(empty window)"]
    ceiling = max((bucket.heat for bucket in strip), default=0.0)
    lines = ["Heat by day"]
    for bucket in strip:
        bar = _bar(bucket.heat, ceiling)
        lines.append(f"{bucket.weekday} {bar} {len(bucket.clips)}")
    peak = peak_day(strip)
    quiet = quiet_days(strip)
    lines.append(f"Peak {peak.weekday} {peak.day.isoformat()}")
    if quiet:
        names = ", ".join(day.strftime("%a") for day in quiet)
        lines.append(f"Quiet {names}")
    return lines


def _bar(heat: float, ceiling: float, width: int = 6) -> str:
    if ceiling <= 0:
        return "░" * width
    filled = int(round(width * min(heat / ceiling, 1.0)))
    filled = min(width, max(0, filled))
    return "█" * filled + "░" * (width - filled)


def _evidence(pulse: Pulse) -> list[str]:
    lines = [EVIDENCE_OPEN, *_theme_lines(pulse), "", "## Crowd"]
    quotes = []
    for clip in pulse.clips:
        for quote in clip.quotes:
            quotes.append(f"- {_clean(quote)} ({clip.lane})")
    lines.extend(quotes[:8] or ["- (no crowd lines this window)"])
    lines.extend(_wow_lines(pulse))
    lines.append(EVIDENCE_CLOSE)
    return lines


def _wow_lines(pulse: Pulse) -> list[str]:
    if not pulse.wow:
        return []
    lines = ["", "## Week-over-week"]
    if pulse.wow.index is not None:
        lines.append(f"Index {pulse.wow.index:.2f} vs prior week")
    lines.append(f"Born {len(pulse.wow.born)} · faded {len(pulse.wow.faded)}")
    for shift in pulse.wow.accelerating[:5]:
        lines.append(f"↑ {_clean(shift.current.title)} ×{shift.ratio:.1f}")
    for shift in pulse.wow.cooling[:5]:
        lines.append(f"↓ {_clean(shift.current.title)} ×{shift.ratio:.1f}")
    return lines


def _theme_lines(pulse: Pulse) -> list[str]:
    lines = ["## Themes"]
    if not pulse.themes:
        lines.append("(no themes)")
        return lines
    for index, theme in enumerate(pulse.themes, start=1):
        lanes = ", ".join(theme.lanes)
        lines.append(f"### {index}. {_clean(theme.title)} ({len(theme.clips)} clips, {lanes})")
        for clip in theme.clips[:4]:
            when = clip.published_at.date().isoformat() if clip.published_at else "?"
            score = clip.engagement.get("score", clip.engagement.get("stars", 0))
            lines.append(f"- [{clip.lane}] {_clean(clip.title)} ({when}, {score}) {_clean(clip.url)}")
            for quote in clip.quotes[:1]:
                lines.append(f"  > {_clean(quote)}")
    return lines


def _coverage(pulse: Pulse) -> list[str]:
    return [COVERAGE_OPEN, "Coverage", *_lane_lines(pulse), COVERAGE_CLOSE]


def _lane_lines(pulse: Pulse) -> list[str]:
    lines = []
    for report in pulse.lanes:
        mass = sum(int(clip.engagement.get("score") or 0) for clip in report.clips)
        status = "ok" if report.ok else "fail"
        extra = f" · {mass} pts" if mass else ""
        lines.append(
            f"  {report.lane:<8} {status} · {len(report.clips)} clips{extra} · {_clean(report.message)}"
        )
    return lines

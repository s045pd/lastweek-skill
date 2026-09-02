from datetime import date, datetime, timezone

import pytest

from engine.window import (
    iso_window,
    monday_window,
    parse_as_of,
    prior_window,
    resolve_window,
    rolling_window,
)


def test_rolling_window_is_seven_inclusive_days():
    week = rolling_window(date(2026, 9, 2))
    assert week.start == date(2026, 8, 27)
    assert week.end == date(2026, 9, 2)
    assert week.kind == "rolling"
    assert len(week.day_list()) == 7


def test_iso_week_uses_monday_sunday_bounds():
    week = iso_window("2026-W36")
    assert week.start == date(2026, 8, 31)
    assert week.end == date(2026, 9, 6)
    assert week.kind == "iso"
    assert week.label == "2026-W36"


def test_iso_week_one_can_start_in_previous_year():
    week = iso_window("2026-W01")
    assert week.start == date(2025, 12, 29)
    assert week.end == date(2026, 1, 4)


def test_iso_week_rejects_bad_spec():
    with pytest.raises(ValueError, match="2026-W36"):
        iso_window("2026W36")
    with pytest.raises(ValueError):
        iso_window("2026-W00")
    with pytest.raises(ValueError):
        iso_window("2026-W54")


def test_monday_window_from_wednesday_is_partial():
    week = monday_window(date(2026, 9, 2))  # Wednesday
    assert week.start == date(2026, 8, 31)
    assert week.end == date(2026, 9, 2)
    assert week.kind == "monday"
    assert len(week.day_list()) == 3


def test_monday_window_on_monday_is_single_day():
    week = monday_window(date(2026, 8, 31))
    assert week.start == week.end == date(2026, 8, 31)


def test_prior_window_shifts_exactly_seven_days():
    current = rolling_window(date(2026, 9, 2))
    previous = prior_window(current)
    assert previous.start == date(2026, 8, 20)
    assert previous.end == date(2026, 8, 26)
    assert previous.kind == "rolling"


def test_prior_of_partial_monday_window_matches_same_weekdays():
    current = monday_window(date(2026, 9, 2))
    previous = prior_window(current)
    assert previous.start == date(2026, 8, 24)
    assert previous.end == date(2026, 8, 26)


def test_resolve_window_iso_flag_wins_over_kind():
    week = resolve_window(kind="rolling", iso_week="2026-W35", as_of="2026-09-02")
    assert week.kind == "iso"
    assert week.start == date(2026, 8, 24)


def test_resolve_window_kind_iso_from_as_of():
    week = resolve_window(kind="iso", as_of="2026-09-02")
    assert week.label == "2026-W36"


def test_parse_as_of_defaults_to_supplied_now():
    now = datetime(2026, 9, 2, 8, 0, tzinfo=timezone.utc)
    assert parse_as_of(None, now=now) == date(2026, 9, 2)
    assert parse_as_of("2026-08-01", now=now) == date(2026, 8, 1)


def test_window_contains_and_rejects_outside():
    week = rolling_window(date(2026, 9, 2))
    assert week.contains(date(2026, 8, 27))
    assert week.contains(datetime(2026, 9, 2, 23, 59, tzinfo=timezone.utc))
    assert not week.contains(date(2026, 8, 26))
    assert not week.contains(date(2026, 9, 3))

from datetime import datetime, timezone

from engine.stamp import parse_stamp


def test_parse_unix_iso_and_rfc2822():
    unix = parse_stamp(1756636800)
    assert unix is not None
    assert unix.tzinfo is not None
    iso = parse_stamp("2026-08-31T12:00:00Z")
    assert iso == datetime(2026, 8, 31, 12, 0, tzinfo=timezone.utc)
    rfc = parse_stamp("Mon, 31 Aug 2026 12:00:00 GMT")
    assert rfc.date().isoformat() == "2026-08-31"
    assert parse_stamp(None) is None
    assert parse_stamp("not a date") is None

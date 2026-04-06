import pytest  # noqa: I001
from datetime import datetime, timezone

from taskwarrior.utils.conversions import parse_taskwarrior_date


def test_parse_compact_format():
    dt = parse_taskwarrior_date("20260101T193139Z")
    assert dt == datetime(2026, 1, 1, 19, 31, 39, tzinfo=timezone.utc)  # noqa: UP017


def test_parse_iso_with_z():
    dt = parse_taskwarrior_date("2026-01-15T14:30:00Z")
    assert dt == datetime(2026, 1, 15, 14, 30, 0, tzinfo=timezone.utc)  # noqa: UP017


def test_parse_without_timezone_returns_naive():
    dt = parse_taskwarrior_date("2026-01-15T14:30:00")
    assert dt == datetime(2026, 1, 15, 14, 30, 0)


def test_parse_invalid_raises_value_error():
    with pytest.raises(ValueError, match="Cannot parse TaskWarrior date"):
        parse_taskwarrior_date("not-a-date")

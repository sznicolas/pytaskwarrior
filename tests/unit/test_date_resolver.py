"""Tests for taskwarrior.utils.date_resolver.

All tests pass an explicit *now* so they are deterministic (no wall-clock
dependency).  The reference point is always a timezone-aware local datetime.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone

from taskwarrior.utils.date_resolver import resolve_date

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# A fixed, unambiguous reference point for all tests:
# 2026-03-15 14:30:00 UTC+2 (a Sunday)
_TZ_PLUS2 = timezone(timedelta(hours=2))
_NOW = datetime(2026, 3, 15, 14, 30, 0, tzinfo=_TZ_PLUS2)  # Sunday, UTC+2


def _utc(*args: int) -> datetime:
    """Create a UTC-aware datetime from positional y/m/d/H/M/S args."""
    return datetime(*args, tzinfo=UTC)


# ---------------------------------------------------------------------------
# ISO 8601 passthrough
# ---------------------------------------------------------------------------


class TestISO8601:
    def test_iso_with_z_suffix(self) -> None:
        dt = resolve_date("2026-01-15T14:30:00Z", _NOW)
        assert dt == _utc(2026, 1, 15, 14, 30, 0)

    def test_iso_with_offset(self) -> None:
        dt = resolve_date("2026-01-15T14:30:00+02:00", _NOW)
        assert dt == _utc(2026, 1, 15, 12, 30, 0)

    def test_iso_naive_treated_as_local(self) -> None:
        # Naive ISO without timezone → interpreted as caller's local tz
        # Resolution is valid (returns UTC-aware datetime)
        dt = resolve_date("2026-06-01T12:00:00", _NOW)
        assert dt is not None
        assert dt.tzinfo == UTC

    def test_date_only_iso(self) -> None:
        dt = resolve_date("2026-06-01", _NOW)
        assert dt is not None
        assert dt.tzinfo == UTC

    def test_unrecognised_returns_none(self) -> None:
        assert resolve_date("next friday", _NOW) is None
        assert resolve_date("invalid", _NOW) is None
        assert resolve_date("today + 2weeks", _NOW) is None


# ---------------------------------------------------------------------------
# Named dates
# ---------------------------------------------------------------------------


class TestNamedDates:
    def test_now(self) -> None:
        dt = resolve_date("now", _NOW)
        assert dt == _NOW.astimezone(UTC)

    def test_today_is_midnight_local(self) -> None:
        dt = resolve_date("today", _NOW)
        # 2026-03-15 00:00 UTC+2 = 2026-03-14 22:00 UTC
        assert dt == _utc(2026, 3, 14, 22, 0, 0)

    def test_tomorrow(self) -> None:
        dt = resolve_date("tomorrow", _NOW)
        # 2026-03-16 00:00 UTC+2 = 2026-03-15 22:00 UTC
        assert dt == _utc(2026, 3, 15, 22, 0, 0)

    def test_yesterday(self) -> None:
        dt = resolve_date("yesterday", _NOW)
        # 2026-03-14 00:00 UTC+2 = 2026-03-13 22:00 UTC
        assert dt == _utc(2026, 3, 13, 22, 0, 0)

    def test_case_insensitive(self) -> None:
        assert resolve_date("TODAY", _NOW) == resolve_date("today", _NOW)
        assert resolve_date("Tomorrow", _NOW) == resolve_date("tomorrow", _NOW)


# ---------------------------------------------------------------------------
# End-of-period
# ---------------------------------------------------------------------------


class TestEndOfPeriod:
    def test_eod(self) -> None:
        dt = resolve_date("eod", _NOW)
        # 2026-03-15 23:59:59 UTC+2 = 2026-03-15 21:59:59 UTC
        assert dt == _utc(2026, 3, 15, 21, 59, 59)

    def test_eow_on_sunday_is_today(self) -> None:
        # _NOW is Sunday — eow should be today 23:59:59
        dt = resolve_date("eow", _NOW)
        assert dt == _utc(2026, 3, 15, 21, 59, 59)

    def test_eow_on_monday_is_next_sunday(self) -> None:
        monday = datetime(2026, 3, 16, 10, 0, 0, tzinfo=_TZ_PLUS2)  # Monday
        dt = resolve_date("eow", monday)
        # 2026-03-22 (Sunday) 23:59:59 UTC+2 = 2026-03-22 21:59:59 UTC
        assert dt == _utc(2026, 3, 22, 21, 59, 59)

    def test_eom(self) -> None:
        dt = resolve_date("eom", _NOW)
        # March 31 23:59:59 UTC+2 = March 31 21:59:59 UTC
        assert dt == _utc(2026, 3, 31, 21, 59, 59)

    def test_eoy(self) -> None:
        dt = resolve_date("eoy", _NOW)
        # Dec 31 23:59:59 UTC+2 = Dec 31 21:59:59 UTC
        assert dt == _utc(2026, 12, 31, 21, 59, 59)


# ---------------------------------------------------------------------------
# Weekday names
# ---------------------------------------------------------------------------


class TestWeekdays:
    def test_monday_from_sunday(self) -> None:
        # _NOW is Sunday; next Monday = 2026-03-16
        dt = resolve_date("monday", _NOW)
        assert dt == _utc(2026, 3, 15, 22, 0, 0)  # Mar 16 00:00 UTC+2

    def test_sunday_from_sunday_is_next_week(self) -> None:
        # If today IS Sunday, "sunday" → next Sunday (+7 days)
        dt = resolve_date("sunday", _NOW)
        assert dt == _utc(2026, 3, 21, 22, 0, 0)  # Mar 22 00:00 UTC+2

    def test_friday_from_sunday(self) -> None:
        # Next Friday from Sunday = +5 days
        dt = resolve_date("friday", _NOW)
        assert dt == _utc(2026, 3, 19, 22, 0, 0)  # Mar 20 00:00 UTC+2


# ---------------------------------------------------------------------------
# Compact relative expressions
# ---------------------------------------------------------------------------


class TestRelative:
    def test_now_plus_days(self) -> None:
        dt = resolve_date("now+2d", _NOW)
        expected = (_NOW + timedelta(days=2)).astimezone(UTC)
        assert dt == expected

    def test_now_minus_days(self) -> None:
        dt = resolve_date("now-1d", _NOW)
        expected = (_NOW - timedelta(days=1)).astimezone(UTC)
        assert dt == expected

    def test_now_plus_weeks(self) -> None:
        dt = resolve_date("now+1w", _NOW)
        expected = (_NOW + timedelta(weeks=1)).astimezone(UTC)
        assert dt == expected

    def test_now_plus_hours(self) -> None:
        dt = resolve_date("now+3h", _NOW)
        expected = (_NOW + timedelta(hours=3)).astimezone(UTC)
        assert dt == expected

    def test_now_plus_months(self) -> None:
        dt = resolve_date("now+1m", _NOW)
        # 2026-03-15 → 2026-04-15
        assert dt is not None
        assert dt.year == 2026
        assert dt.month == 4
        assert dt.day == 15

    def test_month_overflow_clipped(self) -> None:
        # Jan 31 + 1 month → Feb 28 (not Feb 31)
        jan31 = datetime(2026, 1, 31, 12, 0, 0, tzinfo=_TZ_PLUS2)
        dt = resolve_date("now+1m", jan31)
        assert dt is not None
        assert dt.month == 2
        assert dt.day == 28

    def test_now_plus_years(self) -> None:
        dt = resolve_date("now+1y", _NOW)
        assert dt is not None
        assert dt.year == 2027
        assert dt.month == 3
        assert dt.day == 15

    def test_leap_year_feb29_plus_1y(self) -> None:
        feb29 = datetime(2024, 2, 29, 12, 0, 0, tzinfo=_TZ_PLUS2)
        dt = resolve_date("now+1y", feb29)
        assert dt is not None
        # 2025 has no Feb 29 → clipped to Feb 28
        assert dt.month == 2
        assert dt.day == 28

    def test_case_insensitive_units(self) -> None:
        assert resolve_date("now+2D", _NOW) == resolve_date("now+2d", _NOW)
        assert resolve_date("now+1W", _NOW) == resolve_date("now+1w", _NOW)


# ---------------------------------------------------------------------------
# ISO 8601 durations (PnX)
# ---------------------------------------------------------------------------


class TestISODurations:
    def test_p2w(self) -> None:
        dt = resolve_date("P2W", _NOW)
        expected = (_NOW + timedelta(weeks=2)).astimezone(UTC)
        assert dt == expected

    def test_p3d(self) -> None:
        dt = resolve_date("P3D", _NOW)
        expected = (_NOW + timedelta(days=3)).astimezone(UTC)
        assert dt == expected

    def test_p1m(self) -> None:
        dt = resolve_date("P1M", _NOW)
        assert dt is not None
        assert dt.month == 4

    def test_p1y(self) -> None:
        dt = resolve_date("P1Y", _NOW)
        assert dt is not None
        assert dt.year == 2027

    def test_lowercase_p(self) -> None:
        assert resolve_date("p2w", _NOW) == resolve_date("P2W", _NOW)


# ---------------------------------------------------------------------------
# Compound expressions: <base> +/- <duration>
# ---------------------------------------------------------------------------


class TestCompound:
    def test_now_plus_iso_day(self) -> None:
        # now + P1D == now + 1d
        dt = resolve_date("now+P1D", _NOW)
        expected = (_NOW + timedelta(days=1)).astimezone(UTC)
        assert dt == expected

    def test_now_plus_iso_day_with_spaces(self) -> None:
        dt = resolve_date("now + P1D", _NOW)
        expected = (_NOW + timedelta(days=1)).astimezone(UTC)
        assert dt == expected

    def test_now_plus_iso_week(self) -> None:
        dt = resolve_date("now+P2W", _NOW)
        expected = (_NOW + timedelta(weeks=2)).astimezone(UTC)
        assert dt == expected

    def test_today_plus_iso_day(self) -> None:
        # today + P1D == tomorrow (midnight)
        dt = resolve_date("today+P1D", _NOW)
        tomorrow = resolve_date("tomorrow", _NOW)
        assert dt == tomorrow

    def test_tomorrow_minus_iso_day(self) -> None:
        # tomorrow - P1D == today (midnight)
        dt = resolve_date("tomorrow-P1D", _NOW)
        today = resolve_date("today", _NOW)
        assert dt == today

    def test_eom_minus_iso_day(self) -> None:
        # eom (Mar 31 23:59:59 UTC+2) - P1D = Mar 30 23:59:59 UTC+2
        dt = resolve_date("eom-P1D", _NOW)
        assert dt is not None
        assert dt == resolve_date("eom", _NOW) - timedelta(days=1)

    def test_eom_plus_compact_day(self) -> None:
        # eom + 1d — mix: named base + compact duration
        dt = resolve_date("eom+1d", _NOW)
        assert dt is not None
        assert dt == resolve_date("eom", _NOW) + timedelta(days=1)

    def test_iso_date_plus_iso_week(self) -> None:
        # 2026-01-01 + P7D
        dt = resolve_date("2026-01-01+P7D", _NOW)
        assert dt is not None
        base = resolve_date("2026-01-01", _NOW)
        assert dt == base + timedelta(weeks=1)

    def test_compound_result_is_utc(self) -> None:
        exprs = ["now+P1D", "today+P2W", "eom-P1D", "now + P1D"]
        for expr in exprs:
            dt = resolve_date(expr, _NOW)
            assert dt is not None, f"Expected result for {expr!r}"
            assert dt.tzinfo == UTC, f"{expr!r} result not UTC"


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    def test_empty_string_returns_none(self) -> None:
        assert resolve_date("", _NOW) is None

    def test_none_like_unknown_returns_none(self) -> None:
        assert resolve_date("1234garbage", _NOW) is None

    def test_all_results_are_utc_aware(self) -> None:
        exprs = [
            "now", "today", "tomorrow", "yesterday",
            "eod", "eow", "eom", "eoy",
            "now+1d", "now-1d", "now+1w", "now+1m", "now+1y",
            "P1W", "P1D", "P1M", "P1Y",
            "monday", "friday",
            "now+P1D", "now + P1D", "today+P2W", "eom-P1D",
        ]
        for expr in exprs:
            result = resolve_date(expr, _NOW)
            assert result is not None, f"Expected result for {expr!r}"
            assert result.tzinfo == UTC, f"{expr!r} result not UTC"

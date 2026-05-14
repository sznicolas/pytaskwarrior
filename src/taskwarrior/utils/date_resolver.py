"""TaskWarrior date expression resolver (stdlib only).

Converts the most common TaskWarrior date/duration expressions to
UTC-aware :class:`~datetime.datetime` objects without requiring the
``task`` binary.

All calendar calculations are performed in the **local timezone**
(matching TaskWarrior's own behaviour) and the result is returned
as a UTC-aware datetime.

Supported expressions
---------------------
* ISO 8601: ``"2026-01-15"``, ``"2026-01-15T14:30:00Z"``, …
* Named: ``"now"``, ``"today"``, ``"tomorrow"``, ``"yesterday"``
* End-of-period: ``"eod"``, ``"eow"``, ``"eom"``, ``"eoy"``
* Relative (compact form): ``"now+2d"``, ``"now-1w"``, ``"now+3h"``,
  ``"now+1m"``, ``"now+1y"``
* ISO 8601 duration from now: ``"P2W"``, ``"P3D"``, ``"P1M"``, ``"P1Y"``
* Weekday names: ``"monday"`` … ``"sunday"`` (next occurrence after today)

Unsupported (returns ``None``)
-------------------------------
* Compound arithmetic with spaces: ``"today + 2weeks"``
* Natural language: ``"next friday"``, ``"4th of July"``
"""

from __future__ import annotations

import re
from calendar import monthrange
from datetime import datetime, timedelta, timezone

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

_WEEKDAYS: dict[str, int] = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}

# Matches compact relative expressions: now+2d, now-1w, now+3h, now+1m, now+1y
_RE_RELATIVE = re.compile(r"^now([+-])(\d+)([hdwmy])$", re.IGNORECASE)

# Matches ISO 8601 duration from now: P2W, P3D, P1M, P1Y
_RE_ISO_DURATION = re.compile(r"^P(\d+)([DWMY])$", re.IGNORECASE)

# Matches compound expressions: <base> +/- <duration>
# Duration may be ISO 8601 (P1D, P2W, P1M, P1Y, P1H) or compact (1d, 2w, 3h, 1m, 1y).
# The base is anything that resolve_date itself can resolve (named dates, ISO dates, etc.).
_RE_COMPOUND = re.compile(
    r"^(.+?)\s*([+-])\s*(P\d+[DWMYH]|\d+[hdwmy])$",
    re.IGNORECASE,
)


def resolve_date(expr: str, now: datetime | None = None) -> datetime | None:
    """Resolve a TaskWarrior date expression to a UTC-aware datetime.

    Parameters
    ----------
    expr:
        The date string to resolve.  May be an ISO 8601 datetime or a
        TaskWarrior date synonym (``"today"``, ``"eom"``, ``"now+2w"``, …).
    now:
        Reference point for relative expressions.  When ``None``, the
        current local time is used.  If supplied, its timezone is used
        for all calendar calculations.

    Returns
    -------
    datetime | None
        UTC-aware datetime, or ``None`` if the expression is not recognised.
    """
    if not expr:
        return None

    # --- Try ISO 8601 first ---
    iso = _try_iso(expr)
    if iso is not None:
        return iso

    # Establish local "now" for all relative calculations
    base: datetime = now if now is not None else datetime.now().astimezone()
    expr_l = expr.strip().lower()

    # --- Named absolute dates ---
    match expr_l:
        case "now":
            return base.astimezone(timezone.utc)
        case "today":
            return _local_midnight(base)
        case "tomorrow":
            return _local_midnight(base + timedelta(days=1))
        case "yesterday":
            return _local_midnight(base - timedelta(days=1))

    # --- End-of-period ---
    match expr_l:
        case "eod":
            return base.replace(hour=23, minute=59, second=59, microsecond=0).astimezone(timezone.utc)
        case "eow":
            return _eow(base)
        case "eom":
            return _eom(base)
        case "eoy":
            return base.replace(month=12, day=31, hour=23, minute=59, second=59, microsecond=0).astimezone(timezone.utc)

    # --- Weekday names (next occurrence after today) ---
    if expr_l in _WEEKDAYS:
        return _next_weekday(base, _WEEKDAYS[expr_l])

    # --- Compact relative: now+2d, now-1w, … ---
    m = _RE_RELATIVE.match(expr.strip())
    if m:
        return _apply_relative(base, m.group(1), int(m.group(2)), m.group(3).lower())

    # --- ISO 8601 duration: P2W, P3D, P1M, P1Y ---
    m2 = _RE_ISO_DURATION.match(expr.strip())
    if m2:
        return _apply_iso_duration(base, int(m2.group(1)), m2.group(2).upper())

    # --- Compound: <base> +/- <duration> ---
    # e.g. "now + P1D", "today+P2W", "eom-P1D", "2026-01-15+P7D", "tomorrow+2d"
    mc = _RE_COMPOUND.match(expr.strip())
    if mc:
        base_expr, sign, dur_str = mc.group(1), mc.group(2), mc.group(3)
        resolved_base = resolve_date(base_expr.strip(), now)
        if resolved_base is not None:
            # Determine if duration is ISO (PnX) or compact (nd)
            m_iso = _RE_ISO_DURATION.match(dur_str)
            if m_iso:
                return _apply_iso_duration(
                    resolved_base.astimezone(base.tzinfo or timezone.utc),
                    int(m_iso.group(1)) * (1 if sign == "+" else -1),
                    m_iso.group(2).upper(),
                )
            m_compact = re.match(r"^(\d+)([hdwmy])$", dur_str, re.IGNORECASE)
            if m_compact:
                return _apply_relative(
                    resolved_base.astimezone(base.tzinfo or timezone.utc),
                    sign,
                    int(m_compact.group(1)),
                    m_compact.group(2).lower(),
                )

    return None


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _try_iso(expr: str) -> datetime | None:
    """Try to parse *expr* as ISO 8601. Returns UTC-aware datetime or None."""
    # Normalise 'Z' suffix
    normalised = expr.strip().replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(normalised)
        if dt.tzinfo is None:
            # Naive datetime — assume local timezone
            dt = dt.astimezone()
        return dt.astimezone(timezone.utc)
    except ValueError:
        return None


def _local_midnight(dt: datetime) -> datetime:
    """Return midnight of *dt* in its own timezone, converted to UTC."""
    return dt.replace(hour=0, minute=0, second=0, microsecond=0).astimezone(timezone.utc)


def _eow(base: datetime) -> datetime:
    """End of current week: Sunday 23:59:59 local time → UTC.

    If today is Sunday, returns today 23:59:59.
    """
    days_until_sunday = (6 - base.weekday()) % 7
    target = base + timedelta(days=days_until_sunday)
    return target.replace(hour=23, minute=59, second=59, microsecond=0).astimezone(timezone.utc)


def _eom(base: datetime) -> datetime:
    """End of month: last day 23:59:59 local time → UTC."""
    last_day = monthrange(base.year, base.month)[1]
    return base.replace(day=last_day, hour=23, minute=59, second=59, microsecond=0).astimezone(timezone.utc)


def _next_weekday(base: datetime, target_wd: int) -> datetime:
    """Next occurrence of *target_wd* (0=Monday…6=Sunday) after today.

    If today IS the target weekday, returns next week's occurrence.
    """
    days_ahead = target_wd - base.weekday()
    if days_ahead <= 0:
        days_ahead += 7
    return _local_midnight(base + timedelta(days=days_ahead))


def _apply_relative(base: datetime, sign: str, n: int, unit: str) -> datetime:
    """Apply a compact relative expression (now+Nx) to *base*."""
    delta = 1 if sign == "+" else -1
    match unit:
        case "h":
            return (base + timedelta(hours=n * delta)).astimezone(timezone.utc)
        case "d":
            return (base + timedelta(days=n * delta)).astimezone(timezone.utc)
        case "w":
            return (base + timedelta(weeks=n * delta)).astimezone(timezone.utc)
        case "m":
            return _add_months(base, n * delta)
        case "y":
            return _add_years(base, n * delta)
    return base.astimezone(timezone.utc)  # unreachable


def _apply_iso_duration(base: datetime, n: int, unit: str) -> datetime:
    """Apply an ISO 8601 duration (PnX) to *base*."""
    match unit:
        case "D":
            return (base + timedelta(days=n)).astimezone(timezone.utc)
        case "W":
            return (base + timedelta(weeks=n)).astimezone(timezone.utc)
        case "M":
            return _add_months(base, n)
        case "Y":
            return _add_years(base, n)
    return base.astimezone(timezone.utc)  # unreachable


def _add_months(base: datetime, months: int) -> datetime:
    """Add *months* calendar months to *base*, clipping to last valid day."""
    total_months = base.month - 1 + months
    year = base.year + total_months // 12
    month = total_months % 12 + 1
    day = min(base.day, monthrange(year, month)[1])
    return base.replace(year=year, month=month, day=day).astimezone(timezone.utc)


def _add_years(base: datetime, years: int) -> datetime:
    """Add *years* to *base*, handling Feb-29 leap-year edge case."""
    try:
        return base.replace(year=base.year + years).astimezone(timezone.utc)
    except ValueError:
        # Feb 29 → Feb 28 in non-leap year
        return base.replace(year=base.year + years, day=28).astimezone(timezone.utc)

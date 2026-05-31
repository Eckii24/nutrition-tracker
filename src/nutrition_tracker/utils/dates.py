from datetime import date, datetime, timedelta

from nutrition_tracker.errors import ValidationError


def parse_timestamp(value: str) -> datetime:
    try:
        normalized = value.replace("Z", "+00:00")
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ValidationError(f"Malformed timestamp: {value}") from exc
    if parsed.tzinfo is None:
        raise ValidationError(f"Timestamp must include timezone: {value}")
    return parsed


def date_from_timestamp(value: str) -> str:
    return parse_timestamp(value).date().isoformat()


def parse_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValidationError(f"Malformed date: {value}") from exc


def parse_iso_week(value: str) -> tuple[int, int]:
    try:
        year_part, week_part = value.split("-W", maxsplit=1)
        year = int(year_part)
        week = int(week_part)
        date.fromisocalendar(year, week, 1)
    except (ValueError, TypeError) as exc:
        raise ValidationError(f"Malformed ISO week: {value}") from exc
    return year, week


def iso_week_dates(value: str) -> list[str]:
    year, week = parse_iso_week(value)
    monday = date.fromisocalendar(year, week, 1)
    return [(monday + timedelta(days=offset)).isoformat() for offset in range(7)]


def iso_week_from_date(value: str) -> str:
    parsed = parse_date(value)
    iso = parsed.isocalendar()
    return f"{iso.year}-W{iso.week:02d}"


def sanitize_timestamp_for_id(value: str) -> str:
    return value.replace(":", "-")

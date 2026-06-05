from __future__ import annotations

from datetime import date, datetime, timedelta

from nutrition_tracker.domain.errors import ValidationError


def parse_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValidationError(f"Invalid date: {value}") from exc


def parse_timestamp(value: str) -> datetime:
    try:
        timestamp = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValidationError(f"Invalid timestamp: {value}") from exc
    if timestamp.tzinfo is None:
        raise ValidationError(f"Timestamp must include timezone offset: {value}")
    return timestamp


def date_from_timestamp(value: str) -> str:
    return parse_timestamp(value).date().isoformat()


def sanitize_timestamp_for_id(value: str) -> str:
    return value.replace(":", "").replace("-", "").replace("+", "plus").replace(".", "")


def parse_iso_week(value: str) -> tuple[int, int]:
    if len(value) != 8 or value[4:6] != "-W":
        raise ValidationError(f"Invalid ISO week: {value}")
    try:
        year = int(value[:4])
        week = int(value[6:])
    except ValueError as exc:
        raise ValidationError(f"Invalid ISO week: {value}") from exc
    if week < 1 or week > 53:
        raise ValidationError(f"Invalid ISO week: {value}")
    return year, week


def iso_week_dates(value: str) -> list[str]:
    year, week = parse_iso_week(value)
    first_day = date.fromisocalendar(year, week, 1)
    return [(first_day + timedelta(days=offset)).isoformat() for offset in range(7)]

from nutrition_tracker.domain.dates import sanitize_timestamp_for_id


def make_event_id(prefix: str, timestamp: str, sequence: int) -> str:
    return f"{prefix}-{sanitize_timestamp_for_id(timestamp)}-{sequence:03d}"

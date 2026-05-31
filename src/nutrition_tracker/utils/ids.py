from nutrition_tracker.utils.dates import sanitize_timestamp_for_id


def next_sequence(existing_ids: list[str], prefix: str) -> int:
    max_seen = 0
    for existing_id in existing_ids:
        if not existing_id.startswith(prefix):
            continue
        suffix = existing_id.removeprefix(prefix)
        try:
            max_seen = max(max_seen, int(suffix))
        except ValueError:
            continue
    return max_seen + 1


def make_event_id(kind: str, timestamp: str, sequence: int) -> str:
    return f"{kind}_{sanitize_timestamp_for_id(timestamp)}_{sequence:03d}"

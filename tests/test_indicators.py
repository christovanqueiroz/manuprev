from datetime import datetime
from types import SimpleNamespace

from app.indicators import calculate_indicators


def build_record(start: str, end: str):
    return SimpleNamespace(
        failure_start=datetime.fromisoformat(start),
        repair_end=datetime.fromisoformat(end),
    )


def test_indicators_with_multiple_records():
    records = [
        build_record("2025-01-01T08:00:00", "2025-01-01T12:00:00"),
        build_record("2025-01-03T08:00:00", "2025-01-03T10:00:00"),
        build_record("2025-01-05T20:00:00", "2025-01-06T00:00:00"),
    ]

    indicators = calculate_indicators(records)

    assert indicators["mttr_hours"] == 3.33
    assert indicators["mtbf_hours"] == 51.0


def test_indicators_with_single_record():
    indicators = calculate_indicators(
        [build_record("2025-01-01T08:00:00", "2025-01-01T10:00:00")]
    )

    assert indicators["mttr_hours"] == 2.0
    assert indicators["mtbf_hours"] is None

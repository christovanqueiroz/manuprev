from __future__ import annotations


def calculate_indicators(records):
    if not records:
        return {"mtbf_hours": None, "mttr_hours": None}

    ordered = sorted(records, key=lambda item: item.failure_start)
    repair_hours = [
        (item.repair_end - item.failure_start).total_seconds() / 3600 for item in ordered
    ]
    mttr = sum(repair_hours) / len(repair_hours)

    if len(ordered) < 2:
        return {"mtbf_hours": None, "mttr_hours": round(mttr, 2)}

    uptimes = []
    for previous, current in zip(ordered[:-1], ordered[1:]):
        uptimes.append((current.failure_start - previous.repair_end).total_seconds() / 3600)

    mtbf = sum(uptimes) / len(uptimes)
    return {"mtbf_hours": round(mtbf, 2), "mttr_hours": round(mttr, 2)}

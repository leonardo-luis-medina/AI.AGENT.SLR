import hashlib
import json
from typing import Any


def fingerprint_record(record: dict[str, Any]) -> str:
    """
    Generate a stable fingerprint for a deal record.

    Identical records produce identical fingerprints.
    Changed records produce different fingerprints.
    """

    if not isinstance(record, dict):
        raise ValueError("Record must be a dictionary.")

    serialized = json.dumps(
        record,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )

    return hashlib.sha256(
        serialized.encode("utf-8")
    ).hexdigest()


def detect_changes(
    records: list[dict],
    previous_fingerprints: dict[str, str],
) -> dict:
    """
    Detect new, updated, and unchanged deals.

    This function does not modify previous_fingerprints.
    """

    new_records = []
    updated_records = []
    unchanged_records = []
    current_fingerprints = {}

    seen_ids = set()

    for record in records:
        if not isinstance(record, dict):
            raise ValueError("Every record must be a dictionary.")

        deal_id = str(record.get("deal_id", "")).strip()

        if not deal_id:
            raise ValueError("Every record must have a deal_id.")

        if deal_id in seen_ids:
            raise ValueError(
                f"Duplicate deal_id detected: {deal_id}"
            )

        seen_ids.add(deal_id)

        fingerprint = fingerprint_record(record)
        current_fingerprints[deal_id] = fingerprint

        previous = previous_fingerprints.get(deal_id)

        if previous is None:
            new_records.append(record)

        elif previous != fingerprint:
            updated_records.append(record)

        else:
            unchanged_records.append(record)

    return {
        "new": new_records,
        "updated": updated_records,
        "unchanged": unchanged_records,
        "fingerprints": current_fingerprints,
        "summary": {
            "new": len(new_records),
            "updated": len(updated_records),
            "unchanged": len(unchanged_records),
            "total": len(records),
        },
    }
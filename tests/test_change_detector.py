import pytest

from backend.integrations.change_detector import (
    fingerprint_record,
    detect_changes,
)


def test_identical_records_have_same_fingerprint():
    first = {
        "deal_id": "DEMO-001",
        "state": "NSW",
        "amount": 12000,
    }

    second = {
        "amount": 12000,
        "state": "NSW",
        "deal_id": "DEMO-001",
    }

    assert fingerprint_record(first) == fingerprint_record(second)


def test_changed_record_has_different_fingerprint():
    first = {
        "deal_id": "DEMO-001",
        "state": "NSW",
    }

    second = {
        "deal_id": "DEMO-001",
        "state": "VIC",
    }

    assert fingerprint_record(first) != fingerprint_record(second)


def test_new_record_detected():
    records = [
        {"deal_id": "DEMO-001", "state": "NSW"},
    ]

    result = detect_changes(records, {})

    assert result["summary"]["new"] == 1
    assert result["summary"]["updated"] == 0
    assert result["summary"]["unchanged"] == 0


def test_updated_record_detected():
    old = {
        "deal_id": "DEMO-001",
        "state": "NSW",
    }

    updated = {
        "deal_id": "DEMO-001",
        "state": "VIC",
    }

    previous = {
        "DEMO-001": fingerprint_record(old),
    }

    result = detect_changes([updated], previous)

    assert result["summary"]["updated"] == 1


def test_unchanged_record_detected():
    record = {
        "deal_id": "DEMO-001",
        "state": "NSW",
    }

    previous = {
        "DEMO-001": fingerprint_record(record),
    }

    result = detect_changes([record], previous)

    assert result["summary"]["unchanged"] == 1


def test_mixed_changes():
    unchanged = {
        "deal_id": "DEMO-001",
        "state": "NSW",
    }

    updated = {
        "deal_id": "DEMO-002",
        "state": "VIC",
    }

    new = {
        "deal_id": "DEMO-003",
        "state": "QLD",
    }

    previous = {
        "DEMO-001": fingerprint_record(unchanged),
        "DEMO-002": fingerprint_record(
            {"deal_id": "DEMO-002", "state": "NSW"}
        ),
    }

    result = detect_changes(
        [unchanged, updated, new],
        previous,
    )

    assert result["summary"] == {
        "new": 1,
        "updated": 1,
        "unchanged": 1,
        "total": 3,
    }


def test_missing_deal_id_rejected():
    with pytest.raises(ValueError, match="deal_id"):
        detect_changes([{"state": "NSW"}], {})


def test_duplicate_deal_id_rejected():
    records = [
        {"deal_id": "DEMO-001"},
        {"deal_id": "DEMO-001"},
    ]

    with pytest.raises(ValueError, match="Duplicate"):
        detect_changes(records, {})


def test_invalid_record_rejected():
    with pytest.raises(ValueError, match="dictionary"):
        detect_changes(["not a dictionary"], {})


def test_previous_state_not_modified():
    record = {
        "deal_id": "DEMO-001",
        "state": "NSW",
    }

    previous = {
        "DEMO-001": "old-fingerprint",
    }

    detect_changes([record], previous)

    assert previous == {
        "DEMO-001": "old-fingerprint",
    }
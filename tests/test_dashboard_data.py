import json

import pytest

from backend.dashboard_data import (
    load_qc_history,
    build_dashboard_metrics,
    build_evaluation_table,
    build_rule_metrics,
)


@pytest.fixture
def sample_entries():
    return [
        {
            "timestamp": "2026-10-16T10:00:00+00:00",
            "deal_id": "DEMO-001",
            "change_type": "NEW",
            "status": "PROCESSED",
            "qc": {
                "overall_status": "PASS",
                "summary": {
                    "PASS": 2,
                    "FAIL": 0,
                    "NEEDS_HUMAN": 0,
                },
                "results": [
                    {"rule": "R01", "status": "PASS"},
                    {"rule": "R02", "status": "PASS"},
                ],
            },
        },
        {
            "timestamp": "2026-10-16T11:00:00+00:00",
            "deal_id": "DEMO-002",
            "change_type": "NEW",
            "status": "PROCESSED",
            "qc": {
                "overall_status": "FAIL",
                "summary": {
                    "PASS": 1,
                    "FAIL": 1,
                    "NEEDS_HUMAN": 0,
                },
                "results": [
                    {"rule": "R01", "status": "PASS"},
                    {"rule": "R02", "status": "FAIL"},
                ],
            },
        },
        {
            "timestamp": "2026-10-16T12:00:00+00:00",
            "deal_id": "DEMO-003",
            "change_type": "NEW",
            "status": "PROCESSED",
            "qc": {
                "overall_status": "NEEDS_HUMAN",
                "summary": {
                    "PASS": 1,
                    "FAIL": 0,
                    "NEEDS_HUMAN": 1,
                },
                "results": [
                    {"rule": "R01", "status": "PASS"},
                    {"rule": "R02", "status": "NEEDS_HUMAN"},
                ],
            },
        },
    ]


def test_missing_history_returns_empty(tmp_path):
    assert load_qc_history(
        tmp_path / "missing.jsonl"
    ) == []


def test_load_history(tmp_path, sample_entries):
    path = tmp_path / "history.jsonl"

    with path.open("w", encoding="utf-8") as file:
        for entry in sample_entries:
            file.write(json.dumps(entry) + "\n")

    loaded = load_qc_history(path)

    assert len(loaded) == 3


def test_unprocessed_history_excluded(
    tmp_path,
    sample_entries,
):
    path = tmp_path / "history.jsonl"

    entries = sample_entries + [
        {
            "deal_id": "DEMO-004",
            "status": "ERROR",
        }
    ]

    with path.open("w", encoding="utf-8") as file:
        for entry in entries:
            file.write(json.dumps(entry) + "\n")

    assert len(load_qc_history(path)) == 3


def test_invalid_json_rejected(tmp_path):
    path = tmp_path / "history.jsonl"
    path.write_text("{invalid}", encoding="utf-8")

    with pytest.raises(ValueError, match="Invalid JSON"):
        load_qc_history(path)


def test_metrics(sample_entries):
    metrics = build_dashboard_metrics(sample_entries)

    assert metrics["total_evaluations"] == 3
    assert metrics["passed"] == 1
    assert metrics["failed"] == 1
    assert metrics["needs_human"] == 1


def test_evaluation_table(sample_entries):
    table = build_evaluation_table(sample_entries)

    assert len(table) == 3
    assert "overall_status" in table.columns
    assert "deal_id" in table.columns


def test_rule_metrics(sample_entries):
    table = build_rule_metrics(sample_entries)

    r02 = table[
        table["rule"] == "R02"
    ].iloc[0]

    assert r02["PASS"] == 1
    assert r02["FAIL"] == 1
    assert r02["NEEDS_HUMAN"] == 1


def test_empty_metrics():
    metrics = build_dashboard_metrics([])

    assert metrics["total_evaluations"] == 0
    assert metrics["passed"] == 0


def test_empty_tables():
    assert build_evaluation_table([]).empty
    assert build_rule_metrics([]).empty
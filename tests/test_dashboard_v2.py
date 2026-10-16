import json

from backend.dashboard_data import (
    build_dashboard_metrics,
    build_evaluation_table,
    build_rule_metrics,
    load_qc_history,
)


def sample_entries():
    return [
        {
            "status": "PROCESSED",
            "timestamp": "2026-10-16T10:00:00Z",
            "deal_id": "DEMO-001",
            "change_type": "NEW",
            "qc": {
                "overall_status": "PASS",
                "summary": {
                    "PASS": 11,
                    "FAIL": 0,
                    "NEEDS_HUMAN": 0,
                },
                "results": [
                    {
                        "rule": "R01",
                        "status": "PASS",
                    }
                ],
            },
        },
        {
            "status": "PROCESSED",
            "timestamp": "2026-10-16T11:00:00Z",
            "deal_id": "DEMO-002",
            "change_type": "UPDATED",
            "qc": {
                "overall_status": "FAIL",
                "summary": {
                    "PASS": 9,
                    "FAIL": 2,
                    "NEEDS_HUMAN": 0,
                },
                "results": [
                    {
                        "rule": "R01",
                        "status": "FAIL",
                    }
                ],
            },
        },
    ]


def test_dashboard_metrics():
    metrics = build_dashboard_metrics(
        sample_entries()
    )

    assert metrics["total_evaluations"] == 2
    assert metrics["passed"] == 1
    assert metrics["failed"] == 1


def test_dashboard_history_table():
    table = build_evaluation_table(
        sample_entries()
    )

    assert len(table) == 2
    assert "overall_status" in table.columns
    assert "deal_id" in table.columns


def test_dashboard_rule_analytics():
    table = build_rule_metrics(
        sample_entries()
    )

    assert len(table) == 1
    assert table.iloc[0]["PASS"] == 1
    assert table.iloc[0]["FAIL"] == 1


def test_history_loader(tmp_path):
    history_file = tmp_path / "history.jsonl"

    with history_file.open(
        "w",
        encoding="utf-8",
    ) as file:
        for entry in sample_entries():
            file.write(
                json.dumps(entry) + "\n"
            )

    loaded = load_qc_history(history_file)

    assert len(loaded) == 2


def test_history_loader_ignores_unprocessed(tmp_path):
    history_file = tmp_path / "history.jsonl"

    entries = sample_entries()

    entries.append(
        {
            "status": "SKIPPED",
            "deal_id": "DEMO-003",
        }
    )

    with history_file.open(
        "w",
        encoding="utf-8",
    ) as file:
        for entry in entries:
            file.write(
                json.dumps(entry) + "\n"
            )

    loaded = load_qc_history(history_file)

    assert len(loaded) == 2
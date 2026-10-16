import json
from unittest.mock import patch

import pytest

from backend.integrations.sheet_monitor import (
    append_history,
    load_state,
    monitor_google_sheet,
    save_state,
)


@pytest.fixture
def paths(tmp_path):
    return (
        tmp_path / "state.json",
        tmp_path / "history.jsonl",
    )


def record(deal_id, state="NSW"):
    return {
        "deal_id": deal_id,
        "state": state,
    }


def mock_qc(item):
    return {
        "deal_id": item["deal_id"],
        "overall_status": "PASS",
    }


def run_cycle(records, paths):
    state_file, history_file = paths

    with patch(
        "backend.integrations.sheet_monitor.fetch_sheet_records",
        return_value=records,
    ), patch(
        "backend.integrations.sheet_monitor.run_external_qc",
        side_effect=mock_qc,
    ):
        return monitor_google_sheet(
            "test-spreadsheet",
            state_file=state_file,
            history_file=history_file,
        )


def test_missing_state_returns_empty(paths):
    state_file, _ = paths

    assert load_state(state_file) == {}


def test_state_survives_reload(paths):
    state_file, _ = paths

    save_state({"DEMO-001": "abc123"}, state_file)

    assert load_state(state_file) == {
        "DEMO-001": "abc123",
    }


def test_invalid_state_rejected(paths):
    state_file, _ = paths

    state_file.write_text(
        json.dumps(["invalid"]),
        encoding="utf-8",
    )

    with pytest.raises(ValueError):
        load_state(state_file)


def test_new_record_processed(paths):
    result = run_cycle(
        [record("DEMO-001")],
        paths,
    )

    assert result["processed"] == 1
    assert result["changes"]["new"] == 1


def test_unchanged_record_skipped(paths):
    run_cycle([record("DEMO-001")], paths)

    result = run_cycle(
        [record("DEMO-001")],
        paths,
    )

    assert result["processed"] == 0
    assert result["changes"]["unchanged"] == 1


def test_updated_record_reprocessed(paths):
    run_cycle([record("DEMO-001", "NSW")], paths)

    result = run_cycle(
        [record("DEMO-001", "VIC")],
        paths,
    )

    assert result["processed"] == 1
    assert result["changes"]["updated"] == 1


def test_history_written(paths):
    run_cycle([record("DEMO-001")], paths)

    _, history_file = paths

    lines = history_file.read_text(
        encoding="utf-8"
    ).splitlines()

    assert len(lines) == 1

    entry = json.loads(lines[0])

    assert entry["deal_id"] == "DEMO-001"
    assert entry["status"] == "PROCESSED"


def test_history_appends(paths):
    _, history_file = paths

    append_history(
        {"deal_id": "DEMO-001"},
        history_file,
    )

    append_history(
        {"deal_id": "DEMO-002"},
        history_file,
    )

    assert len(
        history_file.read_text(
            encoding="utf-8"
        ).splitlines()
    ) == 2


def test_failed_record_retried(paths):
    state_file, history_file = paths

    with patch(
        "backend.integrations.sheet_monitor.fetch_sheet_records",
        return_value=[record("DEMO-001")],
    ), patch(
        "backend.integrations.sheet_monitor.run_external_qc",
        side_effect=RuntimeError("Temporary error"),
    ):
        first = monitor_google_sheet(
            "test-spreadsheet",
            state_file=state_file,
            history_file=history_file,
        )

    assert first["errors"] == 1

    second = run_cycle(
        [record("DEMO-001")],
        paths,
    )

    assert second["processed"] == 1
    assert second["changes"]["new"] == 1


def test_missing_record_not_deleted(paths):
    run_cycle([record("DEMO-001")], paths)

    run_cycle([], paths)

    state_file, _ = paths

    assert "DEMO-001" in load_state(state_file)


def test_multiple_records_processed(paths):
    result = run_cycle(
        [
            record("DEMO-001"),
            record("DEMO-002"),
            record("DEMO-003"),
        ],
        paths,
    )

    assert result["processed"] == 3


def test_missing_spreadsheet_id_rejected(paths):
    state_file, history_file = paths

    with pytest.raises(ValueError, match="spreadsheet_id"):
        monitor_google_sheet(
            "",
            state_file=state_file,
            history_file=history_file,
        )


def test_invalid_fingerprint_values_rejected(paths):
    state_file, _ = paths

    state_file.write_text(
        json.dumps({"DEMO-001": 123}),
        encoding="utf-8",
    )

    with pytest.raises(ValueError):
        load_state(state_file)
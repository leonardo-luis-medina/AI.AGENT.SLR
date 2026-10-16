import threading

import pytest

from backend.integrations.auto_monitor import run_polling_loop


def test_single_successful_cycle():
    calls = []

    def monitor_fn(**kwargs):
        calls.append(kwargs)

        return {
            "records_found": 3,
            "processed": 0,
            "errors": 0,
        }

    result = run_polling_loop(
        spreadsheet_id="test-sheet",
        interval_seconds=1,
        max_cycles=1,
        monitor_fn=monitor_fn,
    )

    assert result["completed_cycles"] == 1
    assert result["successful_cycles"] == 1
    assert result["failed_cycles"] == 0
    assert len(calls) == 1


def test_multiple_cycles():
    calls = []

    def monitor_fn(**kwargs):
        calls.append(kwargs)

        return {
            "records_found": 3,
            "processed": 0,
            "errors": 0,
        }

    result = run_polling_loop(
        spreadsheet_id="test-sheet",
        interval_seconds=1,
        max_cycles=3,
        monitor_fn=monitor_fn,
    )

    assert result["completed_cycles"] == 3
    assert result["successful_cycles"] == 3
    assert len(calls) == 3


def test_cycle_error_does_not_stop_monitor():
    calls = []

    def monitor_fn(**kwargs):
        calls.append(1)

        if len(calls) == 1:
            raise RuntimeError("Temporary API failure")

        return {
            "records_found": 3,
            "processed": 0,
            "errors": 0,
        }

    result = run_polling_loop(
        spreadsheet_id="test-sheet",
        interval_seconds=1,
        max_cycles=2,
        monitor_fn=monitor_fn,
    )

    assert result["completed_cycles"] == 2
    assert result["failed_cycles"] == 1
    assert result["successful_cycles"] == 1


def test_record_errors_count_as_failed_cycle():
    def monitor_fn(**kwargs):
        return {
            "records_found": 3,
            "processed": 2,
            "errors": 1,
        }

    result = run_polling_loop(
        spreadsheet_id="test-sheet",
        interval_seconds=1,
        max_cycles=1,
        monitor_fn=monitor_fn,
    )

    assert result["failed_cycles"] == 1


def test_pre_stopped_event():
    stop_event = threading.Event()
    stop_event.set()

    result = run_polling_loop(
        spreadsheet_id="test-sheet",
        stop_event=stop_event,
        max_cycles=3,
    )

    assert result["completed_cycles"] == 0


def test_missing_spreadsheet_id():
    with pytest.raises(ValueError, match="spreadsheet_id"):
        run_polling_loop(
            spreadsheet_id="",
            max_cycles=1,
        )


def test_invalid_interval():
    with pytest.raises(ValueError, match="interval_seconds"):
        run_polling_loop(
            spreadsheet_id="test-sheet",
            interval_seconds=0,
            max_cycles=1,
        )


def test_invalid_max_cycles():
    with pytest.raises(ValueError, match="max_cycles"):
        run_polling_loop(
            spreadsheet_id="test-sheet",
            max_cycles=0,
        )


def test_custom_sheet_range_passed():
    received = []

    def monitor_fn(**kwargs):
        received.append(kwargs)

        return {
            "records_found": 0,
            "processed": 0,
            "errors": 0,
        }

    run_polling_loop(
        spreadsheet_id="test-sheet",
        sheet_range="Deals!A1:Z100",
        max_cycles=1,
        monitor_fn=monitor_fn,
    )

    assert received[0]["sheet_range"] == "Deals!A1:Z100"
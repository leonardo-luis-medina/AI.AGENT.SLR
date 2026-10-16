import logging
import threading
from datetime import datetime, timezone

from backend.integrations.sheet_monitor import monitor_google_sheet


logger = logging.getLogger(__name__)


def run_polling_loop(
    spreadsheet_id: str,
    sheet_range: str = "Sheet1!A1:P100",
    interval_seconds: int = 300,
    stop_event: threading.Event | None = None,
    max_cycles: int | None = None,
    monitor_fn=None,
):
    """
    Run repeated Google Sheets monitoring cycles.

    Each cycle completes before the next one starts.
    A stop event allows graceful shutdown.
    """

    if not spreadsheet_id or not spreadsheet_id.strip():
        raise ValueError("spreadsheet_id is required.")

    if interval_seconds < 1:
        raise ValueError("interval_seconds must be at least 1.")

    if max_cycles is not None and max_cycles < 1:
        raise ValueError("max_cycles must be at least 1.")

    if stop_event is None:
        stop_event = threading.Event()

    if monitor_fn is None:
        monitor_fn = monitor_google_sheet

    completed_cycles = 0
    successful_cycles = 0
    failed_cycles = 0

    while not stop_event.is_set():
        completed_cycles += 1

        timestamp = datetime.now(timezone.utc).isoformat()

        logger.info(
            "Starting monitoring cycle %s at %s",
            completed_cycles,
            timestamp,
        )

        try:
            result = monitor_fn(
                spreadsheet_id=spreadsheet_id,
                sheet_range=sheet_range,
            )

            if result.get("errors", 0):
                failed_cycles += 1

                logger.warning(
                    "Cycle %s completed with %s record errors.",
                    completed_cycles,
                    result["errors"],
                )
            else:
                successful_cycles += 1

            logger.info(
                "Cycle %s: found=%s, processed=%s, errors=%s",
                completed_cycles,
                result.get("records_found", 0),
                result.get("processed", 0),
                result.get("errors", 0),
            )

        except Exception:
            failed_cycles += 1

            logger.exception(
                "Monitoring cycle %s failed. Will retry.",
                completed_cycles,
            )

        if max_cycles is not None and completed_cycles >= max_cycles:
            break

        stop_event.wait(interval_seconds)

    return {
        "completed_cycles": completed_cycles,
        "successful_cycles": successful_cycles,
        "failed_cycles": failed_cycles,
        "stopped": True,
    }
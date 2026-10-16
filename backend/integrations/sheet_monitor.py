import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from backend.integrations.change_detector import detect_changes
from backend.integrations.google_sheets import fetch_sheet_records
from backend.integrations.external_qc import run_external_qc


DATA_DIR = Path("data/monitoring")
STATE_FILE = DATA_DIR / "sheet_state.json"
HISTORY_FILE = DATA_DIR / "qc_history.jsonl"


def load_state(state_file=STATE_FILE):
    """Load previously processed record fingerprints."""

    path = Path(state_file)

    if not path.exists():
        return {}

    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, dict):
        raise ValueError("Monitoring state must be a dictionary.")

    if not all(
        isinstance(key, str) and isinstance(value, str)
        for key, value in data.items()
    ):
        raise ValueError("Monitoring state contains invalid fingerprints.")

    return data


def save_state(fingerprints, state_file=STATE_FILE):
    """Save monitoring state using an atomic file replacement."""

    path = Path(state_file)
    path.parent.mkdir(parents=True, exist_ok=True)

    temporary_path = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=".solarqc_state_",
            suffix=".tmp",
            delete=False,
        ) as file:
            temporary_path = Path(file.name)

            json.dump(
                fingerprints,
                file,
                indent=2,
                sort_keys=True,
            )

        os.replace(temporary_path, path)

    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def append_history(entry, history_file=HISTORY_FILE):
    """Append one QC result to the local history file."""

    path = Path(history_file)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("a", encoding="utf-8") as file:
        file.write(
            json.dumps(entry, default=str) + "\n"
        )


def monitor_google_sheet(
    spreadsheet_id,
    sheet_range="Sheet1!A1:P100",
    state_file=STATE_FILE,
    history_file=HISTORY_FILE,
):
    """
    Run one monitoring cycle.

    Only new and updated records are evaluated.
    Successfully evaluated records are remembered.
    Failed records are retried on the next cycle.
    """

    if not spreadsheet_id or not str(spreadsheet_id).strip():
        raise ValueError("spreadsheet_id is required.")

    records = fetch_sheet_records(
        spreadsheet_id,
        sheet_range,
    )

    previous = load_state(state_file)

    changes = detect_changes(records, previous)

    successful_fingerprints = previous.copy()
    results = []

    changed_records = (
        [(record, "NEW") for record in changes["new"]]
        + [(record, "UPDATED") for record in changes["updated"]]
    )

    for record, change_type in changed_records:
        deal_id = str(record["deal_id"]).strip()

        try:
            qc_result = run_external_qc(record)

            entry = {
                "timestamp": datetime.now(
                    timezone.utc
                ).isoformat(),
                "source": "google_sheets",
                "deal_id": deal_id,
                "change_type": change_type,
                "status": "PROCESSED",
                "qc": qc_result,
            }

            append_history(entry, history_file)

            successful_fingerprints[deal_id] = (
                changes["fingerprints"][deal_id]
            )

            results.append(entry)

        except Exception as exc:
            results.append(
                {
                    "deal_id": deal_id,
                    "change_type": change_type,
                    "status": "ERROR",
                    "error_type": type(exc).__name__,
                }
            )

    # Preserve previous fingerprints for records not returned by the sheet.
    # A missing row is not treated as a deletion.
    save_state(successful_fingerprints, state_file)

    return {
        "source": "google_sheets",
        "records_found": len(records),
        "changes": changes["summary"],
        "processed": sum(
            item["status"] == "PROCESSED"
            for item in results
        ),
        "errors": sum(
            item["status"] == "ERROR"
            for item in results
        ),
        "results": results,
    }
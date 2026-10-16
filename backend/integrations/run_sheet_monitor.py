import argparse
import json
import sys

from backend.integrations.sheet_monitor import monitor_google_sheet


def main():
    parser = argparse.ArgumentParser(
        description="Run one SolarQC Google Sheets monitoring cycle."
    )

    parser.add_argument(
        "--spreadsheet-id",
        required=True,
        help="Google Sheets spreadsheet ID",
    )

    parser.add_argument(
        "--range",
        default="Sheet1!A1:P100",
        dest="sheet_range",
        help="Google Sheets range",
    )

    args = parser.parse_args()

    try:
        result = monitor_google_sheet(
            spreadsheet_id=args.spreadsheet_id,
            sheet_range=args.sheet_range,
        )

        print(json.dumps(result, indent=2, default=str))

        if result["errors"]:
            return 1

        return 0

    except Exception as exc:
        print(
            f"Monitoring failed: {type(exc).__name__}",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
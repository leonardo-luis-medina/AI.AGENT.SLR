import argparse
import logging
import threading

from backend.integrations.auto_monitor import run_polling_loop


def main():
    parser = argparse.ArgumentParser(
        description="Start automatic SolarQC Google Sheets monitoring."
    )

    parser.add_argument(
        "--spreadsheet-id",
        required=True,
    )

    parser.add_argument(
        "--range",
        default="Sheet1!A1:P100",
        dest="sheet_range",
    )

    parser.add_argument(
        "--interval",
        type=int,
        default=300,
        help="Seconds between monitoring cycles (default: 300).",
    )

    parser.add_argument(
        "--max-cycles",
        type=int,
        default=None,
        help="Optional number of cycles before stopping.",
    )

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )

    stop_event = threading.Event()

    print("\nSolarQC Automatic Monitoring")
    print("----------------------------")
    print(f"Interval: {args.interval} seconds")
    print("Press Ctrl+C to stop.\n")

    try:
        result = run_polling_loop(
            spreadsheet_id=args.spreadsheet_id,
            sheet_range=args.sheet_range,
            interval_seconds=args.interval,
            stop_event=stop_event,
            max_cycles=args.max_cycles,
        )

        print("\nMonitoring summary:")
        print(result)

    except KeyboardInterrupt:
        stop_event.set()
        print("\nSolarQC monitoring stopped by user.")


if __name__ == "__main__":
    main()
import os

from dotenv import load_dotenv
from backend.integrations.google_sheets import fetch_sheet_records


def main():
    load_dotenv()

    spreadsheet_id = os.getenv("GOOGLE_SPREADSHEET_ID")

    if not spreadsheet_id:
        raise ValueError(
            "GOOGLE_SPREADSHEET_ID is missing from .env"
        )

    print("Connecting to Google Sheets...")

    records = fetch_sheet_records(
        spreadsheet_id,
        "Sheet1!A1:P100",
    )

    print("Connection successful!")
    print(f"Records retrieved: {len(records)}")

    for record in records[:3]:
        print(
            f"Deal: {record.get('deal_id')} | "
            f"Customer: {record.get('customer_name')} | "
            f"State: {record.get('state')}"
        )


if __name__ == "__main__":
    main()
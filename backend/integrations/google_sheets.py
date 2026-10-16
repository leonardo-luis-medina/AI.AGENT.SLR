import os

from dotenv import load_dotenv
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

load_dotenv()

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly"
]


def get_google_sheets_service():
    """Create an authenticated Google Sheets API client."""




    credentials_path = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE")

    if credentials_path and not os.path.isfile(credentials_path):
        raise FileNotFoundError(
            "Google service account credentials file was not found."
        )




    if not credentials_path:
        raise ValueError(
            "GOOGLE_SERVICE_ACCOUNT_FILE is not configured."
        )

    credentials = Credentials.from_service_account_file(
        credentials_path,
        scopes=SCOPES,
    )

    return build(
        "sheets",
        "v4",
        credentials=credentials,
        cache_discovery=False,
    )


def fetch_sheet_records(
    spreadsheet_id,
    sheet_range="Sheet1!A1:Z1000",
):
    """Retrieve Google Sheets rows as dictionaries."""

    if not spreadsheet_id:
        raise ValueError("Spreadsheet ID is required.")

    service = get_google_sheets_service()

    response = (
        service.spreadsheets()
        .values()
        .get(
            spreadsheetId=spreadsheet_id,
            range=sheet_range,
        )
        .execute()
    )

    values = response.get("values", [])

    if not values:
        return []

    headers = values[0]

    records = []

    for row in values[1:]:
        record = {
            header: row[index] if index < len(row) else ""
            for index, header in enumerate(headers)
        }

        records.append(record)

    return records
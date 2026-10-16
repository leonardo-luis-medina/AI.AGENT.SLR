from unittest.mock import patch, MagicMock

import pytest

from backend.integrations.google_sheets import (
    fetch_sheet_records,
)

from backend.integrations.hubspot import (
    fetch_hubspot_deals,
)

from backend.integrations.normalizer import (
    normalize_google_sheet_deal,
    normalize_hubspot_deal,
)


@patch(
    "backend.integrations.google_sheets.get_google_sheets_service"
)
def test_google_sheets_fetch(mock_service):
    service = MagicMock()

    mock_service.return_value = service

    service.spreadsheets.return_value.values.return_value.get.return_value.execute.return_value = {
        "values": [
            ["deal_id", "customer_name", "state"],
            ["DEAL-001", "Test Customer", "NSW"],
        ]
    }

    records = fetch_sheet_records("test-spreadsheet")

    assert len(records) == 1
    assert records[0]["deal_id"] == "DEAL-001"


@patch("backend.integrations.hubspot.requests.get")
@patch.dict(
    "os.environ",
    {"HUBSPOT_ACCESS_TOKEN": "test-token"},
)
def test_hubspot_fetch(mock_get):
    response = MagicMock()

    response.json.return_value = {
        "results": [
            {
                "id": "123",
                "properties": {
                    "dealname": "Test Solar Deal",
                    "amount": "10000",
                },
            }
        ]
    }

    mock_get.return_value = response

    records = fetch_hubspot_deals()

    assert len(records) == 1
    assert records[0]["id"] == "123"


def test_google_sheet_normalization():
    record = {
        "deal_id": "DEAL-001",
        "customer_name": "Test Customer",
        "state": "NSW",
    }

    result = normalize_google_sheet_deal(record)

    assert result["deal_id"] == "DEAL-001"
    assert result["state"] == "NSW"


def test_hubspot_normalization():
    record = {
        "id": "123",
        "properties": {
            "dealname": "Test Solar Deal",
            "amount": "10000",
            "dealstage": "appointmentscheduled",
        },
    }

    result = normalize_hubspot_deal(record)

    assert result["deal_id"] == "123"
    assert result["mapping_status"] == "PARTIAL"


def test_invalid_google_sheet_record():
    with pytest.raises(ValueError):
        normalize_google_sheet_deal(None)


def test_invalid_hubspot_record():
    with pytest.raises(ValueError):
        normalize_hubspot_deal(None)


def test_hubspot_invalid_limit():
    with patch.dict(
        "os.environ",
        {"HUBSPOT_ACCESS_TOKEN": "test-token"},
    ):
        with pytest.raises(ValueError):
            fetch_hubspot_deals(limit=101)
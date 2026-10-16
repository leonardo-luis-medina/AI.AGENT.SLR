from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.main import app


client = TestClient(app)


# ============================================================
# GOOGLE SHEETS API TESTS
# ============================================================

def test_google_sheets_qc_success():
    records = [
        {"deal_id": "DEMO-001"},
        {"deal_id": "DEMO-002"},
    ]

    qc_result = {
        "deal_id": "DEMO-001",
        "overall_status": "PASS",
        "summary": {
            "PASS": 11,
            "FAIL": 0,
            "NEEDS_HUMAN": 0,
        },
    }

    with patch(
        "backend.main.fetch_sheet_records",
        return_value=records,
    ), patch(
        "backend.main.run_external_qc",
        return_value=qc_result,
    ):
        response = client.post(
            "/integrations/google-sheets/qc",
            params={
                "spreadsheet_id": "test-spreadsheet",
                "sheet_range": "Sheet1!A1:P100",
            },
        )

    assert response.status_code == 200

    data = response.json()

    assert data["source"] == "google_sheets"
    assert data["records_processed"] == 2
    assert len(data["results"]) == 2

    assert data["results"][0]["status"] == "PROCESSED"
    assert data["results"][0]["row"] == 2
    assert data["results"][1]["row"] == 3


def test_google_sheets_invalid_record():
    records = [
        {"deal_id": "INVALID-001"},
    ]

    with patch(
        "backend.main.fetch_sheet_records",
        return_value=records,
    ), patch(
        "backend.main.run_external_qc",
        side_effect=ValueError("Missing spreadsheet columns"),
    ):
        response = client.post(
            "/integrations/google-sheets/qc",
            params={
                "spreadsheet_id": "test-spreadsheet",
            },
        )

    assert response.status_code == 200

    data = response.json()

    assert data["records_processed"] == 1
    assert data["results"][0]["status"] == "INVALID_RECORD"
    assert "Missing spreadsheet columns" in data["results"][0]["error"]


def test_google_sheets_service_failure():
    with patch(
        "backend.main.fetch_sheet_records",
        side_effect=RuntimeError("Google Sheets unavailable"),
    ):
        response = client.post(
            "/integrations/google-sheets/qc",
            params={
                "spreadsheet_id": "test-spreadsheet",
            },
        )

    assert response.status_code == 502

    assert response.json()["detail"] == (
        "Unable to retrieve Google Sheets records."
    )


def test_google_sheets_missing_spreadsheet_id():
    response = client.post(
        "/integrations/google-sheets/qc",
    )

    assert response.status_code == 422


def test_google_sheets_empty_spreadsheet():
    with patch(
        "backend.main.fetch_sheet_records",
        return_value=[],
    ):
        response = client.post(
            "/integrations/google-sheets/qc",
            params={
                "spreadsheet_id": "test-spreadsheet",
            },
        )

    assert response.status_code == 200

    data = response.json()

    assert data["records_processed"] == 0
    assert data["results"] == []


# ============================================================
# HUBSPOT API TESTS
# ============================================================

def test_hubspot_qc_success():
    qc_result = {
        "deal_id": "DEMO-004",
        "overall_status": "PASS",
        "summary": {
            "PASS": 11,
            "FAIL": 0,
            "NEEDS_HUMAN": 0,
        },
    }

    with patch(
        "backend.main.run_hubspot_qc",
        return_value=qc_result,
    ):
        response = client.post(
            "/integrations/hubspot/qc",
            params={
                "deal_id": "DEMO-004",
            },
        )

    assert response.status_code == 200

    data = response.json()

    assert data["source"] == "hubspot"
    assert data["deal_id"] == "DEMO-004"
    assert data["qc"]["overall_status"] == "PASS"
    assert data["qc"]["summary"]["PASS"] == 11


def test_hubspot_invalid_deal():
    with patch(
        "backend.main.run_hubspot_qc",
        side_effect=ValueError("Deal not found"),
    ):
        response = client.post(
            "/integrations/hubspot/qc",
            params={
                "deal_id": "UNKNOWN-001",
            },
        )

    assert response.status_code == 400
    assert response.json()["detail"] == "Deal not found"


def test_hubspot_service_failure():
    with patch(
        "backend.main.run_hubspot_qc",
        side_effect=RuntimeError("HubSpot unavailable"),
    ):
        response = client.post(
            "/integrations/hubspot/qc",
            params={
                "deal_id": "DEMO-004",
            },
        )

    assert response.status_code == 502

    assert response.json()["detail"] == (
        "Unable to process HubSpot QC request."
    )


def test_hubspot_default_deal():
    qc_result = {
        "deal_id": "DEMO-004",
        "overall_status": "PASS",
    }

    with patch(
        "backend.main.run_hubspot_qc",
        return_value=qc_result,
    ) as mock_qc:
        response = client.post(
            "/integrations/hubspot/qc",
        )

    assert response.status_code == 200
    assert response.json()["deal_id"] == "DEMO-004"

    mock_qc.assert_called_once_with("DEMO-004")


# ============================================================
# API RESPONSE CONSISTENCY
# ============================================================

def test_hubspot_qc_response_structure():
    qc_result = {
        "deal_id": "DEMO-004",
        "overall_status": "FAIL",
        "summary": {
            "PASS": 9,
            "FAIL": 2,
            "NEEDS_HUMAN": 0,
        },
        "results": [],
        "execution_trace": [],
        "rules_executed": 11,
    }

    with patch(
        "backend.main.run_hubspot_qc",
        return_value=qc_result,
    ):
        response = client.post(
            "/integrations/hubspot/qc",
            params={
                "deal_id": "DEMO-004",
            },
        )

    assert response.status_code == 200

    data = response.json()

    assert "source" in data
    assert "deal_id" in data
    assert "qc" in data

    assert data["qc"]["overall_status"] == "FAIL"
    assert data["qc"]["rules_executed"] == 11
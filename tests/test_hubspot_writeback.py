from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.integrations.hubspot_writeback import (
    build_qc_note,
    qc_fingerprint,
    resolve_hubspot_deal_id,
    find_existing_qc_note,
    create_hubspot_note,
)


TEST_API_KEY = "solarqc-writeback-test-key"

client = TestClient(
    app,
    headers={"X-API-Key": TEST_API_KEY},
)


@pytest.fixture(autouse=True)
def configure_test_api_key(monkeypatch):
    monkeypatch.setenv("SOLARQC_API_KEY", TEST_API_KEY)


MOCK_QC = {
    "deal_id": "DEMO-004",
    "overall_status": "PASS",
    "summary": {
        "PASS": 11,
        "FAIL": 0,
        "NEEDS_HUMAN": 0,
    },
    "results": [],
}


def mock_response(data):
    response = Mock()
    response.json.return_value = data
    response.raise_for_status.return_value = None
    return response


def test_dry_run_does_not_write():
    with patch(
        "backend.main.run_hubspot_qc",
        return_value=MOCK_QC,
    ), patch(
        "backend.main.create_hubspot_note",
    ) as mock_write, patch(
        "backend.main.resolve_hubspot_deal_id",
    ) as mock_resolve:

        response = client.post(
            "/integrations/hubspot/qc/writeback",
        )

    assert response.status_code == 200
    assert response.json()["mode"] == "DRY_RUN"
    assert response.json()["written"] is False
    assert "note_preview" in response.json()

    mock_write.assert_not_called()
    mock_resolve.assert_not_called()


def test_live_writeback_success():
    with patch(
        "backend.main.run_hubspot_qc",
        return_value=MOCK_QC,
    ), patch(
        "backend.main.resolve_hubspot_deal_id",
        return_value="987654",
    ), patch(
        "backend.main.find_existing_qc_note",
        return_value=None,
    ), patch(
        "backend.main.create_hubspot_note",
        return_value={"id": "123456"},
    ) as mock_write:

        response = client.post(
            "/integrations/hubspot/qc/writeback",
            params={"dry_run": "false"},
        )

    assert response.status_code == 200
    assert response.json()["written"] is True
    assert response.json()["hubspot_deal_id"] == "987654"
    assert response.json()["hubspot_note_id"] == "123456"

    mock_write.assert_called_once()


def test_duplicate_note_is_not_created():
    with patch(
        "backend.main.run_hubspot_qc",
        return_value=MOCK_QC,
    ), patch(
        "backend.main.resolve_hubspot_deal_id",
        return_value="987654",
    ), patch(
        "backend.main.find_existing_qc_note",
        return_value="123456",
    ), patch(
        "backend.main.create_hubspot_note",
    ) as mock_write:

        response = client.post(
            "/integrations/hubspot/qc/writeback",
            params={"dry_run": "false"},
        )

    assert response.status_code == 200
    assert response.json()["written"] is False
    assert response.json()["duplicate"] is True
    assert response.json()["hubspot_note_id"] == "123456"

    mock_write.assert_not_called()


def test_invalid_deal():
    with patch(
        "backend.main.run_hubspot_qc",
        side_effect=ValueError("Deal not found"),
    ):
        response = client.post(
            "/integrations/hubspot/qc/writeback",
        )

    assert response.status_code == 400


def test_deal_resolution_failure():
    with patch(
        "backend.main.run_hubspot_qc",
        return_value=MOCK_QC,
    ), patch(
        "backend.main.resolve_hubspot_deal_id",
        side_effect=ValueError("Multiple HubSpot deals match DEMO-004."),
    ):
        response = client.post(
            "/integrations/hubspot/qc/writeback",
            params={"dry_run": "false"},
        )

    assert response.status_code == 400


def test_hubspot_write_failure():
    with patch(
        "backend.main.run_hubspot_qc",
        return_value=MOCK_QC,
    ), patch(
        "backend.main.resolve_hubspot_deal_id",
        return_value="987654",
    ), patch(
        "backend.main.find_existing_qc_note",
        return_value=None,
    ), patch(
        "backend.main.create_hubspot_note",
        side_effect=RuntimeError("HubSpot unavailable"),
    ):
        response = client.post(
            "/integrations/hubspot/qc/writeback",
            params={"dry_run": "false"},
        )

    assert response.status_code == 502


def test_missing_api_key():
    with TestClient(app) as unauthenticated_client:
        response = unauthenticated_client.post(
            "/integrations/hubspot/qc/writeback",
        )

    assert response.status_code == 401


def test_invalid_api_key():
    with TestClient(app) as unauthenticated_client:
        response = unauthenticated_client.post(
            "/integrations/hubspot/qc/writeback",
            headers={"X-API-Key": "incorrect"},
        )

    assert response.status_code == 401


def test_note_contains_fingerprint():
    note = build_qc_note("DEMO-004", MOCK_QC)
    fingerprint = qc_fingerprint("DEMO-004", MOCK_QC)

    assert f"Fingerprint: {fingerprint}" in note
    assert "DEMO-004" in note
    assert "regulatory certification" in note


def test_fingerprint_is_stable():
    first = qc_fingerprint("DEMO-004", MOCK_QC)
    second = qc_fingerprint("DEMO-004", MOCK_QC)

    assert first == second
    assert len(first) == 16


def test_resolve_hubspot_deal_id():
    response = mock_response(
        {
            "results": [
                {
                    "id": "987654",
                    "properties": {
                        "solarqc_deal_id": "DEMO-004",
                    },
                }
            ]
        }
    )

    with patch(
        "backend.integrations.hubspot_writeback.requests.post",
        return_value=response,
    ) as mock_post, patch(
        "backend.integrations.hubspot_writeback._headers",
        return_value={},
    ):
        deal_id = resolve_hubspot_deal_id("DEMO-004")

    assert deal_id == "987654"
    mock_post.assert_called_once()


def test_resolve_rejects_multiple_matches():
    response = mock_response(
        {
            "results": [
                {
                    "id": "111",
                    "properties": {"solarqc_deal_id": "DEMO-004"},
                },
                {
                    "id": "222",
                    "properties": {"solarqc_deal_id": "DEMO-004"},
                },
            ]
        }
    )

    with patch(
        "backend.integrations.hubspot_writeback.requests.post",
        return_value=response,
    ), patch(
        "backend.integrations.hubspot_writeback._headers",
        return_value={},
    ):
        with pytest.raises(ValueError, match="Multiple"):
            resolve_hubspot_deal_id("DEMO-004")


def test_existing_note_detection():
    association_response = mock_response(
        {
            "results": [{"id": "123456"}],
        }
    )

    note_response = mock_response(
        {
            "properties": {
                "hs_note_body": "SolarQC<br>Fingerprint: abc123",
            }
        }
    )

    with patch(
        "backend.integrations.hubspot_writeback.requests.get",
        side_effect=[association_response, note_response],
    ), patch(
        "backend.integrations.hubspot_writeback._headers",
        return_value={},
    ):
        note_id = find_existing_qc_note("987654", "abc123")

    assert note_id == "123456"


def test_existing_note_not_found():
    response = mock_response({"results": []})

    with patch(
        "backend.integrations.hubspot_writeback.requests.get",
        return_value=response,
    ), patch(
        "backend.integrations.hubspot_writeback._headers",
        return_value={},
    ):
        note_id = find_existing_qc_note("987654", "abc123")

    assert note_id is None


def test_create_note_association():
    response = mock_response({"id": "123456"})

    with patch(
        "backend.integrations.hubspot_writeback.requests.post",
        return_value=response,
    ) as mock_post, patch(
        "backend.integrations.hubspot_writeback._headers",
        return_value={},
    ):
        result = create_hubspot_note(
            hubspot_deal_id="987654",
            note_body="SolarQC test note",
        )

    assert result["id"] == "123456"

    payload = mock_post.call_args.kwargs["json"]

    assert payload["associations"][0]["to"]["id"] == "987654"
    assert payload["associations"][0]["types"][0][
        "associationTypeId"
    ] == 202
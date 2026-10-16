import json
from unittest.mock import patch

import pytest
import requests

from backend.integrations.hubspot_qc import (
    fetch_hubspot_qc_deal,
    normalize_hubspot_qc_deal,
    run_hubspot_qc,
)


def sample_properties():
    return {
        "dealname": "SolarQC DEMO-004",
        "amount": "12000",
        "solarqc_deal_id": "DEMO-004",
        "solarqc_customer_name": "Jordan Parker",
        "solarqc_state": "NSW",
        "solarqc_postcode": "2000",
        "solarqc_system_size_kw": "6.6",
        "solarqc_roof_type": "tile",
        "solarqc_payment_method": "cash",
        "solarqc_deposit_amount": "1200",
        "solarqc_sale_date": "2026-10-16",
        "solarqc_signature_date": "2026-10-16",
        "solarqc_installation_date": "2026-11-10",
        "description": json.dumps({
            "contract_received": True,
            "electricity_bill_received": True,
            "switchboard_photo_received": True,
            "sales_notes": "Customer confirmed roof access.",
            "sales_status": "Sold",
        }),
    }


def test_normalize_hubspot_deal():
    result = normalize_hubspot_qc_deal(sample_properties())

    assert result["deal_id"] == "DEMO-004"
    assert result["total_price"] == "12000"
    assert result["payment_type"] == "cash"
    assert result["stage"] == "Sold"
    assert result["switchboard_photo_received"] is True


def test_invalid_description_json():
    properties = sample_properties()
    properties["description"] = "{invalid}"

    with pytest.raises(ValueError, match="invalid JSON"):
        normalize_hubspot_qc_deal(properties)


def test_description_must_be_object():
    properties = sample_properties()
    properties["description"] = "[]"

    with pytest.raises(ValueError, match="JSON object"):
        normalize_hubspot_qc_deal(properties)


def test_missing_token():
    with patch.dict("os.environ", {"HUBSPOT_ACCESS_TOKEN": ""}):
        with pytest.raises(ValueError, match="HUBSPOT_ACCESS_TOKEN"):
            fetch_hubspot_qc_deal()


def test_fetch_hubspot_deal():
    mock_response = requests.Response()
    mock_response.status_code = 200
    mock_response._content = json.dumps({
        "results": [
            {"properties": sample_properties()}
        ]
    }).encode()

    with patch.dict("os.environ", {"HUBSPOT_ACCESS_TOKEN": "fake-test-token"}):
        with patch(
            "backend.integrations.hubspot_qc.requests.get",
            return_value=mock_response,
        ):
            result = fetch_hubspot_qc_deal("DEMO-004")

    assert result["solarqc_deal_id"] == "DEMO-004"


def test_hubspot_deal_not_found():
    mock_response = requests.Response()
    mock_response.status_code = 200
    mock_response._content = b'{"results": []}'

    with patch.dict("os.environ", {"HUBSPOT_ACCESS_TOKEN": "fake-test-token"}):
        with patch(
            "backend.integrations.hubspot_qc.requests.get",
            return_value=mock_response,
        ):
            with pytest.raises(ValueError, match="not found"):
                fetch_hubspot_qc_deal("DEMO-999")


def test_hubspot_api_error():
    with patch.dict("os.environ", {"HUBSPOT_ACCESS_TOKEN": "fake-test-token"}):
        with patch(
            "backend.integrations.hubspot_qc.requests.get",
            side_effect=requests.ConnectionError("Network unavailable"),
        ):
            with pytest.raises(requests.ConnectionError):
                fetch_hubspot_qc_deal()


def test_run_hubspot_qc():
    expected = {
        "deal_id": "DEMO-004",
        "overall_status": "PASS",
        "rules_executed": 11,
    }

    with patch(
        "backend.integrations.hubspot_qc.fetch_hubspot_qc_deal",
        return_value=sample_properties(),
    ):
        with patch(
            "backend.integrations.hubspot_qc.run_external_qc",
            return_value=expected,
        ) as mock_qc:
            result = run_hubspot_qc("DEMO-004")

    assert result == expected
    mock_qc.assert_called_once()
    assert mock_qc.call_args.args[0]["deal_id"] == "DEMO-004"
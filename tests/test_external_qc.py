from unittest.mock import patch

import pytest

from backend.integrations.external_qc import (
    convert_boolean,
    convert_number,
    validate_date,
    prepare_google_sheet_deal,
    run_external_qc,
)


@pytest.fixture
def sample_record():
    return {
        "deal_id": "DEMO-001",
        "customer_name": "Alex Morgan",
        "state": "NSW",
        "postcode": "2000",
        "roof_type": "tile",
        "system_size_kw": "6.6",
        "payment_type": "cash",
        "total_price": "10000",
        "deposit_amount": "1000",
        "sale_date": "2026-10-01",
        "signature_date": "2026-10-01",
        "requested_install_date": "2026-10-20",
        "stage": "Sold",
        "switchboard_photo_received": "TRUE",
        "electricity_bill_received": "TRUE",
        "notes": "Customer confirmed roof access.",
    }


def test_boolean_conversion():
    assert convert_boolean("TRUE") is True
    assert convert_boolean("FALSE") is False
    assert convert_boolean("yes") is True


def test_invalid_boolean():
    with pytest.raises(ValueError):
        convert_boolean("maybe")


def test_number_conversion():
    assert convert_number("6.6") == 6.6
    assert convert_number("10000") == 10000.0


def test_invalid_number():
    with pytest.raises(ValueError):
        convert_number("unknown")


def test_valid_date():
    assert validate_date("2026-10-01") == "2026-10-01"


def test_invalid_date():
    with pytest.raises(ValueError):
        validate_date("2026-99-99")


def test_prepare_google_sheet_deal(sample_record):
    deal = prepare_google_sheet_deal(sample_record)

    assert deal["deal_id"] == "DEMO-001"
    assert deal["system_size_kw"] == 6.6
    assert deal["switchboard_photo_received"] is True


def test_missing_columns(sample_record):
    del sample_record["roof_type"]

    with pytest.raises(ValueError):
        prepare_google_sheet_deal(sample_record)


@patch("backend.integrations.external_qc.execute_agent")
def test_external_qc_calls_agent(mock_agent, sample_record):
    mock_agent.return_value = {
        "overall_status": "PASS",
        "rules_executed": 11,
    }

    result = run_external_qc(sample_record)

    assert result["overall_status"] == "PASS"
    mock_agent.assert_called_once()
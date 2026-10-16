from copy import deepcopy
from unittest.mock import patch

import pytest

from backend.integrations.external_qc import run_external_qc


@pytest.fixture
def valid_deal():
    return {
        "deal_id": "DEMO-TEST-001",
        "customer_name": "Jordan Parker",
        "state": "NSW",
        "postcode": "2000",
        "system_size_kw": "6.6",
        "roof_type": "tile",
        "payment_type": "cash",
        "deposit_amount": "1200",
        "total_price": "12000",
        "sale_date": "2026-10-16",
        "signature_date": "2026-10-16",
        "requested_install_date": "2026-11-10",
        "contract_received": True,
        "electricity_bill_received": True,
        "switchboard_photo_received": True,
        "notes": "Customer confirmed roof access.",
        "stage": "Sold",
    }


def run_rule(deal, rule):
    return run_external_qc(deal, selected_rules=[rule])


def test_insufficient_cash_deposit(valid_deal):
    deal = deepcopy(valid_deal)
    deal["deposit_amount"] = "100"

    result = run_rule(deal, "R05")

    assert result["results"][0]["rule"] == "R05"
    assert result["results"][0]["result"] == "FAIL"


def test_invalid_state(valid_deal):
    deal = deepcopy(valid_deal)
    deal["state"] = "XX"

    result = run_rule(deal, "R03")

    assert result["results"][0]["result"] == "FAIL"


def test_invalid_roof_type(valid_deal):
    deal = deepcopy(valid_deal)
    deal["roof_type"] = "unknown-roof"

    result = run_rule(deal, "R04")

    assert result["results"][0]["result"] == "FAIL"


def test_signature_after_sale(valid_deal):
    deal = deepcopy(valid_deal)
    deal["signature_date"] = "2026-10-20"

    result = run_rule(deal, "R06")

    assert result["results"][0]["result"] == "FAIL"


def test_installation_too_early(valid_deal):
    deal = deepcopy(valid_deal)
    deal["requested_install_date"] = "2026-10-18"

    result = run_rule(deal, "R07")

    assert result["results"][0]["result"] == "FAIL"


def test_missing_electricity_bill(valid_deal):
    deal = deepcopy(valid_deal)
    deal["electricity_bill_received"] = False

    result = run_rule(deal, "R08")

    assert result["results"][0]["result"] == "FAIL"


def test_contract_not_required_by_r08(valid_deal):
    deal = deepcopy(valid_deal)
    deal["contract_received"] = False

    result = run_rule(deal, "R08")

    assert result["results"][0]["rule"] == "R08"
    assert result["results"][0]["result"] == "PASS"


def test_invalid_postcode_state_pair(valid_deal):
    deal = deepcopy(valid_deal)
    deal["state"] = "VIC"
    deal["postcode"] = "2000"

    result = run_rule(deal, "R09")

    assert result["results"][0]["result"] == "FAIL"


def test_missing_required_column(valid_deal):
    deal = deepcopy(valid_deal)
    del deal["customer_name"]

    with pytest.raises(ValueError, match="Missing spreadsheet columns"):
        run_external_qc(deal)


def test_invalid_numeric_value(valid_deal):
    deal = deepcopy(valid_deal)
    deal["system_size_kw"] = "not-a-number"

    with pytest.raises(ValueError):
        run_external_qc(deal)


def test_invalid_date_format(valid_deal):
    deal = deepcopy(valid_deal)
    deal["sale_date"] = "16/10/2026"

    with pytest.raises(ValueError):
        run_external_qc(deal)
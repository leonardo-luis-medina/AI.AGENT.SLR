from unittest.mock import patch

from backend.tools import (
    check_system_size,
    check_required_fields,
    check_state,
    check_roof_type,
    check_cash_deposit,
    check_signature_date,
    check_install_date,
    check_sold_documents,
    check_postcode_state,
)

def test_r01_valid_system_size():
    result = check_system_size("DEAL-003")
    assert result["result"] == "PASS"


def test_r01_invalid_system_size():
    invalid_deal = {
        "deal_id": "DEAL-003",
        "system_size_kw": 0
    }

    with patch("backend.tools.get_deal", return_value=invalid_deal):
        result = check_system_size("DEAL-003")

    assert result["result"] == "FAIL"


def test_r01_missing_deal():
    result = check_system_size("DEAL-999")
    assert "error" in result

def test_r02_valid_deal():
    result = check_required_fields("DEAL-001")
    assert result["result"] == "PASS"


def test_r02_missing_customer_name():
    incomplete_deal = {
        "deal_id": "DEAL-001",
        "customer_name": "",
        "state": "NSW",
        "system_size_kw": 6.6,
        "roof_type": "tile"
    }

    with patch("backend.tools.get_deal", return_value=incomplete_deal):
        result = check_required_fields("DEAL-001")

    assert result["result"] == "FAIL"
    assert "customer_name" in result["reason"]


def test_r02_missing_deal():
    result = check_required_fields("DEAL-999")
    assert "error" in result

def test_r03_valid_state():
    result = check_state("DEAL-001")
    assert result["result"] == "PASS"


def test_r03_invalid_state():
    invalid_deal = {
        "deal_id": "DEAL-001",
        "state": "XYZ"
    }

    with patch("backend.tools.get_deal", return_value=invalid_deal):
        result = check_state("DEAL-001")

    assert result["result"] == "FAIL"


def test_r03_missing_state():
    incomplete_deal = {
        "deal_id": "DEAL-001"
    }

    with patch("backend.tools.get_deal", return_value=incomplete_deal):
        result = check_state("DEAL-001")

    assert result["result"] == "FAIL"

def test_r04_valid_roof_type():
    result = check_roof_type("DEAL-001")
    assert result["result"] == "PASS"


def test_r04_invalid_roof_type():
    invalid_deal = {
        "deal_id": "DEAL-001",
        "roof_type": "unknown"
    }

    with patch("backend.tools.get_deal", return_value=invalid_deal):
        result = check_roof_type("DEAL-001")

    assert result["result"] == "FAIL"


def test_r04_missing_roof_type():
    incomplete_deal = {
        "deal_id": "DEAL-001"
    }

    with patch("backend.tools.get_deal", return_value=incomplete_deal):
        result = check_roof_type("DEAL-001")

    assert result["result"] == "FAIL"

# R05 — Cash deposit

def test_r05_pass():
    deal = {
        "payment_type": "cash",
        "total_price": 10000,
        "deposit_amount": 500
    }
    with patch("backend.tools.get_deal", return_value=deal):
        assert check_cash_deposit("TEST")["result"] == "PASS"


def test_r05_fail():
    deal = {
        "payment_type": "cash",
        "total_price": 10000,
        "deposit_amount": 400
    }
    with patch("backend.tools.get_deal", return_value=deal):
        assert check_cash_deposit("TEST")["result"] == "FAIL"


def test_r05_missing_data():
    deal = {"payment_type": "cash"}
    with patch("backend.tools.get_deal", return_value=deal):
        assert check_cash_deposit("TEST")["result"] == "NEEDS_HUMAN"


# R06 — Signature date

def test_r06_pass():
    deal = {
        "signature_date": "2026-10-01",
        "sale_date": "2026-10-02"
    }
    with patch("backend.tools.get_deal", return_value=deal):
        assert check_signature_date("TEST")["result"] == "PASS"


def test_r06_fail():
    deal = {
        "signature_date": "2026-10-03",
        "sale_date": "2026-10-02"
    }
    with patch("backend.tools.get_deal", return_value=deal):
        assert check_signature_date("TEST")["result"] == "FAIL"


def test_r06_missing_data():
    with patch("backend.tools.get_deal", return_value={}):
        assert check_signature_date("TEST")["result"] == "NEEDS_HUMAN"


# R07 — Installation date

def test_r07_pass():
    deal = {
        "sale_date": "2026-10-01",
        "requested_install_date": "2026-10-08"
    }
    with patch("backend.tools.get_deal", return_value=deal):
        assert check_install_date("TEST")["result"] == "PASS"


def test_r07_fail():
    deal = {
        "sale_date": "2026-10-01",
        "requested_install_date": "2026-10-05"
    }
    with patch("backend.tools.get_deal", return_value=deal):
        assert check_install_date("TEST")["result"] == "FAIL"


def test_r07_missing_data():
    with patch("backend.tools.get_deal", return_value={}):
        assert check_install_date("TEST")["result"] == "NEEDS_HUMAN"


# R08 — Required documents

def test_r08_pass():
    deal = {
        "stage": "Sold",
        "switchboard_photo_received": True,
        "electricity_bill_received": True
    }
    with patch("backend.tools.get_deal", return_value=deal):
        assert check_sold_documents("TEST")["result"] == "PASS"


def test_r08_fail():
    deal = {
        "stage": "Sold",
        "switchboard_photo_received": False,
        "electricity_bill_received": True
    }
    with patch("backend.tools.get_deal", return_value=deal):
        assert check_sold_documents("TEST")["result"] == "FAIL"


def test_r08_missing_data():
    with patch("backend.tools.get_deal", return_value={}):
        assert check_sold_documents("TEST")["result"] == "NEEDS_HUMAN"


# R09 — Postcode/state

def test_r09_pass():
    deal = {"state": "NSW", "postcode": "2000"}
    with patch("backend.tools.get_deal", return_value=deal):
        assert check_postcode_state("TEST")["result"] == "PASS"


def test_r09_fail():
    deal = {"state": "NSW", "postcode": "3000"}
    with patch("backend.tools.get_deal", return_value=deal):
        assert check_postcode_state("TEST")["result"] == "FAIL"


def test_r09_missing_data():
    deal = {"state": "NSW"}
    with patch("backend.tools.get_deal", return_value=deal):
        assert check_postcode_state("TEST")["result"] == "NEEDS_HUMAN"
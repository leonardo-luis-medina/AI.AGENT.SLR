from unittest.mock import patch
from backend.tools import check_system_size, check_required_fields


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
from unittest.mock import patch

from backend.qc_runner import run_all_qc


@patch("backend.qc_runner.analyze_deal_notes")
@patch("backend.qc_runner.get_deal")
def test_run_all_qc_pass(mock_get_deal, mock_ai):
    mock_get_deal.return_value = {"deal_id": "TEST-001"}

    mock_ai.return_value = {
        "R10": {"result": "PASS", "reason": "No issues."},
        "R11": {"result": "PASS", "reason": "No contradictions."},
    }

    with patch(
        "backend.qc_runner.check_system_size",
        return_value={"rule": "R01", "result": "PASS"},
    ), patch(
        "backend.qc_runner.check_required_fields",
        return_value={"rule": "R02", "result": "PASS"},
    ), patch(
        "backend.qc_runner.check_state",
        return_value={"rule": "R03", "result": "PASS"},
    ), patch(
        "backend.qc_runner.check_roof_type",
        return_value={"rule": "R04", "result": "PASS"},
    ), patch(
        "backend.qc_runner.check_cash_deposit",
        return_value={"rule": "R05", "result": "PASS"},
    ), patch(
        "backend.qc_runner.check_signature_date",
        return_value={"rule": "R06", "result": "PASS"},
    ), patch(
        "backend.qc_runner.check_install_date",
        return_value={"rule": "R07", "result": "PASS"},
    ), patch(
        "backend.qc_runner.check_sold_documents",
        return_value={"rule": "R08", "result": "PASS"},
    ), patch(
        "backend.qc_runner.check_postcode_state",
        return_value={"rule": "R09", "result": "PASS"},
    ):
        result = run_all_qc("TEST-001")

    assert result["overall_status"] == "PASS"
    assert result["summary"]["PASS"] == 11
    assert len(result["results"]) == 11


@patch("backend.qc_runner.get_deal")
def test_run_all_qc_missing_deal(mock_get_deal):
    mock_get_deal.return_value = {"error": "Deal not found"}

    result = run_all_qc("UNKNOWN")

    assert "error" in result
    assert result["deal_id"] == "UNKNOWN"
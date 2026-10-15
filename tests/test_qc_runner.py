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
        "backend.qc_runner.CHECKS",
        [
            lambda deal_id, i=i: {
                "rule": f"R{i:02d}",
                "result": "PASS",
                "reason": "Valid",
            }
            for i in range(1, 10)
        ],
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


@patch("backend.qc_runner.analyze_deal_notes")
@patch("backend.qc_runner.get_deal")
def test_qc_runner_handles_ai_failure(mock_get_deal, mock_ai):
    mock_get_deal.return_value = {
        "deal_id": "TEST-001",
        "notes": "Installation access is clear.",
    }

    mock_ai.side_effect = RuntimeError("Unexpected AI failure")

    from backend.qc_runner import CHECKS

    with patch(
        "backend.qc_runner.CHECKS",
        [
            lambda deal_id: {
                "rule": f"R{i:02d}",
                "result": "PASS",
                "reason": "Valid",
            }
            for i in range(1, 10)
        ],
    ):
        result = run_all_qc("TEST-001")

    assert result["overall_status"] == "NEEDS_HUMAN"
    assert result["summary"]["PASS"] == 9
    assert result["summary"]["NEEDS_HUMAN"] == 2
    assert len(result["results"]) == 11
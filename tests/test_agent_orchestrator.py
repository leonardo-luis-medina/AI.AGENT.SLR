from unittest.mock import patch

from backend.agent_orchestrator import execute_agent


@patch("backend.agent_orchestrator.get_deal")
def test_agent_runs_multiple_tools(mock_get_deal):
    mock_get_deal.return_value = {"deal_id": "TEST-001"}

    fake_rules = {
        f"R{i:02d}": (
            lambda deal_id, i=i: {
                "rule": f"R{i:02d}",
                "result": "PASS",
                "reason": "Valid",
            }
        )
        for i in range(1, 4)
    }

    with patch(
        "backend.agent_orchestrator.RULE_FUNCTIONS",
        fake_rules,
    ):
        result = execute_agent(
            "TEST-001",
            selected_rules=["R01", "R02", "R03"],
        )

    assert result["rules_executed"] == 3
    assert result["overall_status"] == "PASS"
    assert result["summary"]["PASS"] == 3
    assert len(result["execution_trace"]) == 3


@patch("backend.agent_orchestrator.get_deal")
def test_agent_invalid_rule(mock_get_deal):
    mock_get_deal.return_value = {"deal_id": "TEST-001"}

    result = execute_agent(
        "TEST-001",
        selected_rules=["R99"],
    )

    assert "error" in result


@patch("backend.agent_orchestrator.get_deal")
def test_agent_missing_deal(mock_get_deal):
    mock_get_deal.return_value = {"error": "Deal not found"}

    result = execute_agent("UNKNOWN")

    assert "error" in result


@patch("backend.agent_orchestrator.get_deal")
@patch("backend.agent_orchestrator.RULE_FUNCTIONS")
def test_agent_tool_failure(mock_rules, mock_get_deal):
    mock_get_deal.return_value = {"deal_id": "TEST-001"}

    mock_rules.__getitem__.side_effect = RuntimeError(
        "Tool failed"
    )

    result = execute_agent(
        "TEST-001",
        selected_rules=["R01"],
    )

    assert result["overall_status"] == "NEEDS_HUMAN"
    assert result["results"][0]["result"] == "NEEDS_HUMAN"


@patch("backend.agent_orchestrator.get_deal")
@patch("backend.agent_orchestrator.analyze_deal_notes")
def test_agent_runs_ai_once(mock_ai, mock_get_deal):
    mock_get_deal.return_value = {
        "deal_id": "TEST-001",
        "notes": "Customer confirmed the roof is tile.",
    }

    mock_ai.return_value = {
        "R10": {"result": "PASS", "reason": "No issues."},
        "R11": {"result": "PASS", "reason": "No contradictions."},
    }

    result = execute_agent(
        "TEST-001",
        selected_rules=["R10", "R11"],
    )

    assert result["rules_executed"] == 2
    assert result["overall_status"] == "PASS"
    mock_ai.assert_called_once()


@patch("backend.agent_orchestrator.get_deal")
@patch("backend.agent_orchestrator.RULE_FUNCTIONS")
def test_agent_attaches_policy(mock_rules, mock_get_deal):
    mock_get_deal.return_value = {"deal_id": "TEST-001"}

    mock_rules.__getitem__.side_effect = lambda rule: (
        lambda deal_id: {
            "rule": rule,
            "result": "PASS",
            "reason": "Valid",
        }
    )

    result = execute_agent(
        "TEST-001",
        selected_rules=["R05"],
    )

    assert result["results"][0]["policy"]["policy_id"] == "POL-005"


@patch("backend.agent_orchestrator.get_deal")
@patch("backend.agent_orchestrator.RULE_FUNCTIONS")


def test_agent_removes_duplicate_rules(mock_rules, mock_get_deal):



    mock_get_deal.return_value = {"deal_id": "TEST-001"}

    mock_rules.__getitem__.side_effect = lambda rule: (
        lambda deal_id: {
            "rule": rule,
            "result": "PASS",
            "reason": "Valid",
        }
    )

    result = execute_agent(
        "TEST-001",
        selected_rules=["R01", "R01", "R02"],
    )

    assert result["rules_executed"] == 2
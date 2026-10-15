from unittest.mock import patch

from backend.llm_checks import analyze_deal_notes


def mock_qwen_response(content):
    from types import SimpleNamespace

    return SimpleNamespace(
        message=SimpleNamespace(content=content)
    )


@patch("backend.llm_checks.client.chat")
def test_unresolved_access_issue(mock_chat):
    mock_chat.return_value = mock_qwen_response(
        '{"R10":{"result":"PASS","reason":"No issue"},'
        '"R11":{"result":"PASS","reason":"No contradiction"}}'
    )

    deal = {
        "roof_type": "tile",
        "notes": (
            "Customer confirmed the roof is metal. "
            "Installation access is blocked and remains unresolved."
        ),
    }

    results = analyze_deal_notes(deal)

    assert results["R10"]["result"] == "FAIL"
    assert results["R11"]["result"] == "FAIL"


@patch("backend.llm_checks.client.chat")
def test_valid_deal(mock_chat):
    mock_chat.return_value = mock_qwen_response(
        '{"R10":{"result":"PASS","reason":"No unresolved issues"},'
        '"R11":{"result":"PASS","reason":"Fields match"}}'
    )

    deal = {
        "roof_type": "tile",
        "notes": (
            "Customer confirmed the roof is tile. "
            "Installation access is clear."
        ),
    }

    results = analyze_deal_notes(deal)

    assert results["R10"]["result"] == "PASS"
    assert results["R11"]["result"] == "PASS"


@patch("backend.llm_checks.client.chat")
def test_missing_notes(mock_chat):
    results = analyze_deal_notes({"roof_type": "tile"})

    assert results["R10"]["result"] == "NEEDS_HUMAN"
    assert results["R11"]["result"] == "NEEDS_HUMAN"

    mock_chat.assert_not_called()
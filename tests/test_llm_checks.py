from unittest.mock import patch

from backend.llm_checks import analyze_deal_notes, validate_ai_results


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


def test_invalid_ai_status():
    results = validate_ai_results({
        "R10": {"result": "APPROVED", "reason": "Looks good."},
        "R11": {"result": "PASS", "reason": "No contradiction."},
    })

    assert results["R10"]["result"] == "NEEDS_HUMAN"
    assert results["R11"]["result"] == "PASS"


def test_missing_ai_rule():
    results = validate_ai_results({
        "R10": {"result": "PASS", "reason": "No issues."}
    })

    assert results["R11"]["result"] == "NEEDS_HUMAN"


def test_invalid_ai_structure():
    results = validate_ai_results({
        "R10": "PASS",
        "R11": None,
    })

    assert results["R10"]["result"] == "NEEDS_HUMAN"
    assert results["R11"]["result"] == "NEEDS_HUMAN"


def test_empty_ai_explanation():
    results = validate_ai_results({
        "R10": {"result": "PASS", "reason": ""},
        "R11": {"result": "FAIL", "reason": "   "},
    })

    assert results["R10"]["result"] == "NEEDS_HUMAN"
    assert results["R11"]["result"] == "NEEDS_HUMAN"

@patch("backend.llm_checks.client.chat")
def test_ollama_unavailable(mock_chat):
    mock_chat.side_effect = ConnectionError("Ollama unavailable")

    deal = {
        "roof_type": "tile",
        "notes": "Customer confirmed the roof is tile."
    }

    results = analyze_deal_notes(deal)

    assert results["R10"]["result"] == "NEEDS_HUMAN"
    assert results["R11"]["result"] == "NEEDS_HUMAN"


@patch("backend.llm_checks.client.chat")
def test_ollama_connection_failure(mock_chat):
    mock_chat.side_effect = ConnectionError("Ollama unavailable")

    deal = {
        "roof_type": "tile",
        "notes": "Customer confirmed the roof is tile.",
    }

    results = analyze_deal_notes(deal)

    assert results["R10"]["result"] == "NEEDS_HUMAN"
    assert results["R11"]["result"] == "NEEDS_HUMAN"


@patch("backend.llm_checks.client.chat")
def test_ollama_timeout(mock_chat):
    mock_chat.side_effect = TimeoutError("Request timed out")

    deal = {
        "roof_type": "tile",
        "notes": "Installation access is clear.",
    }

    results = analyze_deal_notes(deal)

    assert results["R10"]["result"] == "NEEDS_HUMAN"
    assert results["R11"]["result"] == "NEEDS_HUMAN"


@patch("backend.llm_checks.client.chat")
def test_invalid_json_response(mock_chat):
    mock_chat.return_value = mock_qwen_response(
        "This is not valid JSON"
    )

    deal = {
        "roof_type": "tile",
        "notes": "Installation access is clear.",
    }

    results = analyze_deal_notes(deal)

    assert results["R10"]["result"] == "NEEDS_HUMAN"
    assert results["R11"]["result"] == "NEEDS_HUMAN"


@patch("backend.llm_checks.client.chat")
def test_unexpected_ai_status(mock_chat):
    mock_chat.return_value = mock_qwen_response(
        '{"R10":{"result":"APPROVED","reason":"Looks fine"},'
        '"R11":{"result":"PASS","reason":"No contradictions"}}'
    )

    deal = {
        "roof_type": "tile",
        "notes": "Customer confirmed the roof is tile.",
    }

    results = analyze_deal_notes(deal)

    assert results["R10"]["result"] == "NEEDS_HUMAN"
    assert results["R11"]["result"] == "PASS"


@patch("backend.llm_checks.client.chat")
def test_conflicting_access_statements(mock_chat):
    mock_chat.return_value = mock_qwen_response(
        '{"R10":{"result":"PASS","reason":"Access resolved"},'
        '"R11":{"result":"PASS","reason":"No contradictions"}}'
    )

    deal = {
        "roof_type": "tile",
        "notes": (
            "Installation access is blocked. "
            "Later update: access issue resolved."
        ),
    }

    results = analyze_deal_notes(deal)

    assert results["R10"]["result"] == "NEEDS_HUMAN"
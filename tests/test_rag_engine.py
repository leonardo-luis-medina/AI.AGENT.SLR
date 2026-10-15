from unittest.mock import patch, MagicMock

from backend.rag_engine import answer_policy_question


@patch("backend.rag_engine.client.chat")
def test_rag_returns_policy_sources(mock_chat):
    response = MagicMock()

    response.message.content = (
        "POL-005 requires a minimum 5% cash deposit."
    )

    mock_chat.return_value = response

    result = answer_policy_question(
        "What is the minimum cash deposit requirement?"
    )

    assert result["status"] == "SUCCESS"
    assert result["sources"]
    assert any(
        source["policy_id"] == "POL-005"
        for source in result["sources"]
    )


@patch("backend.rag_engine.client.chat")
def test_rag_handles_ai_failure(mock_chat):
    mock_chat.side_effect = ConnectionError(
        "Ollama unavailable"
    )

    result = answer_policy_question(
        "What is the minimum cash deposit requirement?"
    )

    assert result["status"] == "AI_UNAVAILABLE"
    assert result["sources"]


def test_rag_empty_question():
    result = answer_policy_question("")

    assert result["status"] == "INVALID_QUESTION"


@patch("backend.rag_engine.retrieve_policies")
def test_rag_no_policy_found(mock_retrieve):
    mock_retrieve.return_value = []

    result = answer_policy_question(
        "Unknown policy question"
    )

    assert result["status"] == "NO_POLICY_FOUND"
    assert result["sources"] == []
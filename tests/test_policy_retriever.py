from backend.policy_retriever import (
    load_policies,
    retrieve_policies,
)


def test_policy_documents_load():
    policies = load_policies()

    assert len(policies) == 11


def test_cash_deposit_policy_retrieval():
    results = retrieve_policies(
        "What is the minimum cash deposit requirement?"
    )

    assert results
    assert results[0]["policy_id"] == "POL-005"


def test_roof_type_policy_retrieval():
    results = retrieve_policies(
        "What roof types are supported?"
    )

    assert results
    assert any(
        item["policy_id"] == "POL-004"
        for item in results
    )


def test_empty_query():
    results = retrieve_policies("")

    assert results == []


def test_unknown_policy():
    results = retrieve_policies(
        "zyxwvutsrqponmlkjihgfedcba"
    )

    assert results == []


def test_retrieval_limit():
    results = retrieve_policies(
        "solar sales customer installation",
        top_k=2,
    )

    assert len(results) <= 2
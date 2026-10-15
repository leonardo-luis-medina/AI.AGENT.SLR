import json
import re
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

POLICY_PATH = BASE_DIR / "knowledge" / "solar_policies.json"


def load_policies():
    """Load the local policy knowledge base."""

    with open(POLICY_PATH, "r", encoding="utf-8") as file:
        return json.load(file)


def tokenize(text):
    """Convert text into searchable words."""

    return set(
        re.findall(r"[a-z0-9]+", str(text).lower())
    )


def retrieve_policies(query, top_k=3):
    """Retrieve policies relevant to a question."""

    if not isinstance(query, str) or not query.strip():
        return []

    if not isinstance(top_k, int) or isinstance(top_k, bool) or top_k < 1:
        return []

    policies = load_policies()

    query_tokens = tokenize(query)

    scored = []

    for policy in policies:
        title_tokens = tokenize(policy["title"])
        content_tokens = tokenize(policy["content"])
        rule_tokens = tokenize(policy["rule"])
        id_tokens = tokenize(policy["policy_id"])

        title_overlap = len(query_tokens & title_tokens)
        content_overlap = len(query_tokens & content_tokens)
        rule_overlap = len(query_tokens & rule_tokens)
        id_overlap = len(query_tokens & id_tokens)

        score = (
            title_overlap * 3
            + content_overlap
            + rule_overlap * 5
            + id_overlap * 5
        )

        if score > 0:
            scored.append((score, policy))

    scored.sort(
        key=lambda item: (-item[0], item[1]["policy_id"])
    )

    return [
        policy
        for score, policy in scored[:top_k]
    ]
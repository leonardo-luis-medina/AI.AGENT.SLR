from datetime import datetime, timezone

from backend.tools import (
    get_deal,
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

from backend.llm_checks import analyze_deal_notes, validate_ai_results
from backend.policy_retriever import load_policies


RULE_FUNCTIONS = {
    "R01": check_system_size,
    "R02": check_required_fields,
    "R03": check_state,
    "R04": check_roof_type,
    "R05": check_cash_deposit,
    "R06": check_signature_date,
    "R07": check_install_date,
    "R08": check_sold_documents,
    "R09": check_postcode_state,
}

ALL_RULES = [f"R{i:02d}" for i in range(1, 12)]


def policy_lookup():
    """Map QC rules to their corresponding policy references."""

    return {
        policy["rule"]: {
            "policy_id": policy["policy_id"],
            "title": policy["title"],
        }
        for policy in load_policies()
    }


def execute_agent(deal_id, selected_rules=None):
    """
    Execute selected QC tools and attach policy references.

    If selected_rules is None, execute all 11 rules.
    """

    deal = get_deal(deal_id)

    if "error" in deal:
        return {
            "deal_id": deal_id,
            "error": deal["error"],
        }

    if selected_rules is None:
        selected_rules = ALL_RULES.copy()

    if (
        not isinstance(selected_rules, list)
        or not selected_rules
        or any(rule not in ALL_RULES for rule in selected_rules)
    ):
        return {
            "deal_id": deal_id,
            "error": "Invalid rule selection.",
        }

    # Remove duplicates while preserving order.
    selected_rules = list(dict.fromkeys(selected_rules))

    policies = policy_lookup()
    results = []
    trace = []

    ai_results = None

    for rule in selected_rules:
        started_at = datetime.now(timezone.utc).isoformat()

        try:
            if rule in RULE_FUNCTIONS:
                result = RULE_FUNCTIONS[rule](deal_id)

            else:
                # R10 and R11 share one AI request.
                if ai_results is None:
                    ai_results = validate_ai_results(
                        analyze_deal_notes(deal)
                    )

                result = {
                    "rule": rule,
                    **ai_results[rule],
                }

            if not isinstance(result, dict):
                raise ValueError("Invalid tool response")

            status = result.get("result")

            if status not in {"PASS", "FAIL", "NEEDS_HUMAN"}:
                raise ValueError("Invalid QC status")

            result = {
                "rule": rule,
                "result": status,
                "reason": result.get("reason", ""),
                "policy": policies.get(rule),
            }

        except Exception:
            result = {
                "rule": rule,
                "result": "NEEDS_HUMAN",
                "reason": "Tool execution failed. Manual review required.",
                "policy": policies.get(rule),
            }

        results.append(result)

        trace.append({
            "rule": rule,
            "started_at": started_at,
            "status": result["result"],
        })

    counts = {
        "PASS": 0,
        "FAIL": 0,
        "NEEDS_HUMAN": 0,
    }

    for item in results:
        counts[item["result"]] += 1

    overall_status = (
        "FAIL" if counts["FAIL"]
        else "NEEDS_HUMAN" if counts["NEEDS_HUMAN"]
        else "PASS"
    )

    return {
        "deal_id": deal_id,
        "overall_status": overall_status,
        "summary": counts,
        "results": results,
        "execution_trace": trace,
        "rules_executed": len(results),
    }
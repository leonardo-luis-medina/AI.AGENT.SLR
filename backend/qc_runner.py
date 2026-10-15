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
from backend.llm_checks import analyze_deal_notes


def run_all_qc(deal_id: str) -> dict:
    """Run all 11 SolarQC quality-control rules."""

    deal = get_deal(deal_id)

    if "error" in deal:
        return {"deal_id": deal_id, "error": deal["error"]}

    checks = [
        check_system_size,
        check_required_fields,
        check_state,
        check_roof_type,
        check_cash_deposit,
        check_signature_date,
        check_install_date,
        check_sold_documents,
        check_postcode_state,
    ]

    results = []

    # R01–R09: Deterministic Python checks
    for check in checks:
        results.append(check(deal_id))

    # R10–R11: AI-assisted checks
    ai_results = analyze_deal_notes(deal)

    for rule in ("R10", "R11"):
        item = ai_results.get(rule, {})

        results.append({
            "rule": rule,
            "result": item.get("result", "NEEDS_HUMAN"),
            "reason": item.get("reason", "AI assessment unavailable."),
        })

    counts = {
        "PASS": 0,
        "FAIL": 0,
        "NEEDS_HUMAN": 0,
    }

    for item in results:
        status = item.get("result", "NEEDS_HUMAN")

        if status not in counts:
            status = "NEEDS_HUMAN"

        counts[status] += 1

    return {
        "deal_id": deal_id,
        "overall_status": (
            "FAIL" if counts["FAIL"] > 0
            else "NEEDS_HUMAN" if counts["NEEDS_HUMAN"] > 0
            else "PASS"
        ),
        "summary": counts,
        "results": results,
    }
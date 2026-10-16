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

from backend.llm_checks import (
    analyze_deal_notes,
    validate_ai_results,
    manual_review,
)


CHECKS = [
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


def run_all_qc(deal_id: str) -> dict:
    """Run all 11 SolarQC quality-control rules."""

    deal = get_deal(deal_id)

    if "error" in deal:
        return {
            "deal_id": deal_id,
            "error": deal["error"],
        }

    results = []

    

# R01-R09: Deterministic Python checks.
    for check in CHECKS:
        results.append(check(deal_id))

    # R10-R11: AI-assisted checks.
    try:
        ai_results = analyze_deal_notes(deal)
        ai_results = validate_ai_results(ai_results)

    except Exception:
        ai_results = manual_review(
            "Unexpected AI assessment error. Manual review required."
        )

    for rule in ("R10", "R11"):
        item = ai_results[rule]

        results.append({
            "rule": rule,
            "result": item["result"],
            "reason": item["reason"],
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
            item["result"] = status
            item["reason"] = "Invalid QC result. Manual review required."

        counts[status] += 1

    if counts["FAIL"]:
        overall_status = "FAIL"

    elif counts["NEEDS_HUMAN"]:
        overall_status = "NEEDS_HUMAN"

    else:
        overall_status = "PASS"

    return {
        "deal_id": deal_id,
        "overall_status": overall_status,
        "summary": counts,
        "results": results,
    }
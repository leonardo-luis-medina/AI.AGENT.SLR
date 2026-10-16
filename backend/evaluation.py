from collections import Counter
from typing import Any


VALID_STATUSES = ("PASS", "FAIL", "NEEDS_HUMAN")


def normalize_status(value: Any) -> str:
    if not isinstance(value, str):
        raise ValueError("QC status must be a string.")

    status = value.strip().upper()

    if status not in VALID_STATUSES:
        raise ValueError(f"Invalid QC status: {value}")

    return status


def safe_divide(numerator: int, denominator: int) -> float:
    return numerator / denominator if denominator else 0.0


def evaluate_predictions(cases: list[dict]) -> dict:
    """
    Compare expected QC decisions with actual decisions.

    Each case must contain:
      - deal_id
      - expected_status
      - predicted_status

    PASS is treated as the positive class.

    A false pass occurs when the expected status is FAIL or
    NEEDS_HUMAN but the predicted status is PASS.
    """

    if not isinstance(cases, list):
        raise ValueError("Evaluation cases must be a list.")

    confusion_matrix = {
        expected: {predicted: 0 for predicted in VALID_STATUSES}
        for expected in VALID_STATUSES
    }

    errors = []
    seen_ids = set()

    for index, case in enumerate(cases):
        if not isinstance(case, dict):
            raise ValueError(f"Case {index} must be a dictionary.")

        deal_id = str(case.get("deal_id", "")).strip()

        if not deal_id:
            raise ValueError(f"Case {index} is missing deal_id.")

        if deal_id in seen_ids:
            raise ValueError(f"Duplicate deal_id: {deal_id}")

        seen_ids.add(deal_id)

        expected = normalize_status(case.get("expected_status"))
        predicted = normalize_status(case.get("predicted_status"))

        confusion_matrix[expected][predicted] += 1

        if expected != predicted:
            errors.append({
                "deal_id": deal_id,
                "expected_status": expected,
                "predicted_status": predicted,
            })

    total = len(cases)
    correct = total - len(errors)

    true_pass = confusion_matrix["PASS"]["PASS"]

    false_pass = (
        confusion_matrix["FAIL"]["PASS"]
        + confusion_matrix["NEEDS_HUMAN"]["PASS"]
    )

    predicted_pass = sum(
        confusion_matrix[expected]["PASS"]
        for expected in VALID_STATUSES
    )

    expected_pass = sum(confusion_matrix["PASS"].values())

    expected_non_pass = total - expected_pass

    human_reviews = sum(
        confusion_matrix[expected]["NEEDS_HUMAN"]
        for expected in VALID_STATUSES
    )

    expected_counts = Counter()
    predicted_counts = Counter()

    for expected in VALID_STATUSES:
        for predicted in VALID_STATUSES:
            count = confusion_matrix[expected][predicted]
            expected_counts[expected] += count
            predicted_counts[predicted] += count

    return {
        "total_cases": total,
        "correct_predictions": correct,
        "incorrect_predictions": len(errors),
        "accuracy": safe_divide(correct, total),
        "false_pass_rate": safe_divide(
            false_pass, expected_non_pass
        ),
        "pass_precision": safe_divide(
            true_pass, predicted_pass
        ),
        "pass_recall": safe_divide(
            true_pass, expected_pass
        ),
        "human_review_rate": safe_divide(
            human_reviews, total
        ),
        "false_pass_count": false_pass,
        "expected_counts": dict(expected_counts),
        "predicted_counts": dict(predicted_counts),
        "confusion_matrix": confusion_matrix,
        "errors": errors,
    }
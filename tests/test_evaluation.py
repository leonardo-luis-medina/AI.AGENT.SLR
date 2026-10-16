import json

import pytest

from backend.evaluation import (
    evaluate_predictions,
    normalize_status,
    safe_divide,
)

from backend.evaluation_report import (
    generate_evaluation_report,
)


def case(deal_id, expected, predicted):
    return {
        "deal_id": deal_id,
        "expected_status": expected,
        "predicted_status": predicted,
    }


def test_normalize_status():
    assert normalize_status(" pass ") == "PASS"


def test_invalid_status_rejected():
    with pytest.raises(ValueError):
        normalize_status("APPROVED")


def test_safe_divide_zero():
    assert safe_divide(1, 0) == 0.0


def test_perfect_predictions():
    cases = [
        case("A", "PASS", "PASS"),
        case("B", "FAIL", "FAIL"),
        case("C", "NEEDS_HUMAN", "NEEDS_HUMAN"),
    ]

    result = evaluate_predictions(cases)

    assert result["accuracy"] == 1.0
    assert result["false_pass_rate"] == 0.0


def test_false_pass_detected():
    cases = [
        case("A", "FAIL", "PASS"),
        case("B", "NEEDS_HUMAN", "PASS"),
    ]

    result = evaluate_predictions(cases)

    assert result["false_pass_count"] == 2
    assert result["false_pass_rate"] == 1.0


def test_confusion_matrix():
    cases = [
        case("A", "PASS", "FAIL"),
        case("B", "FAIL", "PASS"),
    ]

    result = evaluate_predictions(cases)

    assert result["confusion_matrix"]["PASS"]["FAIL"] == 1
    assert result["confusion_matrix"]["FAIL"]["PASS"] == 1


def test_duplicate_deal_rejected():
    cases = [
        case("A", "PASS", "PASS"),
        case("A", "FAIL", "FAIL"),
    ]

    with pytest.raises(ValueError, match="Duplicate"):
        evaluate_predictions(cases)


def test_missing_deal_id_rejected():
    with pytest.raises(ValueError, match="deal_id"):
        evaluate_predictions([
            {
                "expected_status": "PASS",
                "predicted_status": "PASS",
            }
        ])


def test_empty_dataset():
    result = evaluate_predictions([])

    assert result["total_cases"] == 0
    assert result["accuracy"] == 0.0


def test_human_review_rate():
    cases = [
        case("A", "PASS", "NEEDS_HUMAN"),
        case("B", "FAIL", "FAIL"),
    ]

    result = evaluate_predictions(cases)

    assert result["human_review_rate"] == 0.5


def test_report_saved(tmp_path):
    cases = [
        case("A", "PASS", "PASS"),
    ]

    report = generate_evaluation_report(
        cases,
        output_dir=tmp_path,
    )

    path = tmp_path / "latest_evaluation.json"

    assert path.exists()

    saved = json.loads(
        path.read_text(encoding="utf-8")
    )

    assert saved["metrics"]["accuracy"] == 1.0
    assert report["metrics"]["total_cases"] == 1


def test_invalid_case_type():
    with pytest.raises(ValueError, match="dictionary"):
        evaluate_predictions(["invalid"])


def test_precision():
    cases = [
        case("A", "PASS", "PASS"),
        case("B", "FAIL", "PASS"),
    ]

    result = evaluate_predictions(cases)

    assert result["pass_precision"] == 0.5


def test_recall():
    cases = [
        case("A", "PASS", "PASS"),
        case("B", "PASS", "FAIL"),
    ]

    result = evaluate_predictions(cases)

    assert result["pass_recall"] == 0.5
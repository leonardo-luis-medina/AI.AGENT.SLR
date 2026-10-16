import pytest

from backend.real_evaluation import evaluate_real_agent


def make_case(deal_id, expected):
    return {
        "expected_status": expected,
        "deal": {
            "deal_id": deal_id,
        },
    }


def fake_qc(status):
    def runner(deal):
        return {
            "deal_id": deal["deal_id"],
            "overall_status": status,
        }

    return runner


def test_real_evaluation_uses_qc_runner():
    cases = [
        make_case("EVAL-001", "PASS"),
    ]

    result = evaluate_real_agent(
        cases,
        qc_runner=fake_qc("PASS"),
    )

    assert result["metrics"]["accuracy"] == 1.0
    assert result["predictions"][0]["predicted_status"] == "PASS"


def test_real_evaluation_detects_wrong_prediction():
    cases = [
        make_case("EVAL-001", "FAIL"),
    ]

    result = evaluate_real_agent(
        cases,
        qc_runner=fake_qc("PASS"),
    )

    assert result["metrics"]["false_pass_count"] == 1


def test_real_evaluation_rejects_manual_prediction():
    cases = [
        {
            **make_case("EVAL-001", "PASS"),
            "predicted_status": "PASS",
        }
    ]

    with pytest.raises(ValueError, match="predicted_status"):
        evaluate_real_agent(
            cases,
            qc_runner=fake_qc("PASS"),
        )


def test_duplicate_deal_rejected():
    cases = [
        make_case("EVAL-001", "PASS"),
        make_case("EVAL-001", "FAIL"),
    ]

    with pytest.raises(ValueError, match="Duplicate"):
        evaluate_real_agent(
            cases,
            qc_runner=fake_qc("PASS"),
        )


def test_missing_deal_rejected():
    with pytest.raises(ValueError, match="deal dictionary"):
        evaluate_real_agent(
            [{"expected_status": "PASS"}],
            qc_runner=fake_qc("PASS"),
        )


def test_missing_deal_id_rejected():
    with pytest.raises(ValueError, match="deal_id"):
        evaluate_real_agent(
            [{
                "expected_status": "PASS",
                "deal": {},
            }],
            qc_runner=fake_qc("PASS"),
        )


def test_invalid_qc_result_rejected():
    cases = [
        make_case("EVAL-001", "PASS"),
    ]

    with pytest.raises(ValueError, match="invalid result"):
        evaluate_real_agent(
            cases,
            qc_runner=lambda deal: None,
        )


def test_empty_dataset():
    result = evaluate_real_agent(
        [],
        qc_runner=fake_qc("PASS"),
    )

    assert result["metrics"]["total_cases"] == 0


def test_human_review_prediction():
    cases = [
        make_case("EVAL-001", "NEEDS_HUMAN"),
    ]

    result = evaluate_real_agent(
        cases,
        qc_runner=fake_qc("NEEDS_HUMAN"),
    )

    assert result["metrics"]["human_review_rate"] == 1.0


def test_invalid_case_rejected():
    with pytest.raises(ValueError, match="dictionary"):
        evaluate_real_agent(
            ["invalid"],
            qc_runner=fake_qc("PASS"),
        )
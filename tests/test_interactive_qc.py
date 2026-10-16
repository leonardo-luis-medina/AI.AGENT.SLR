from copy import deepcopy

import pytest

from backend import interactive_qc


def test_sample_deals_available():
    samples = interactive_qc.get_sample_deals()

    assert len(samples) == 3


def test_samples_are_independent_copies():
    first = interactive_qc.get_sample_deals()

    first["Complete Sale"]["customer_name"] = "Changed"

    second = interactive_qc.get_sample_deals()

    assert (
        second["Complete Sale"]["customer_name"]
        == "Jordan Parker"
    )


def test_deterministic_mode_selects_nine_rules(monkeypatch):
    captured = {}

    def fake_run(record, selected_rules=None):
        captured["rules"] = selected_rules

        return {
            "deal_id": record["deal_id"],
            "overall_status": "PASS",
            "summary": {
                "PASS": 9,
                "FAIL": 0,
                "NEEDS_HUMAN": 0,
            },
            "results": [],
            "rules_executed": 9,
        }

    monkeypatch.setattr(
        interactive_qc,
        "run_external_qc",
        fake_run,
    )

    sample = interactive_qc.get_sample_deals()[
        "Complete Sale"
    ]

    result = interactive_qc.run_interactive_qc(
        sample,
        mode="deterministic",
    )

    assert captured["rules"] == [
        f"R{i:02d}" for i in range(1, 10)
    ]

    assert result["qc"]["rules_executed"] == 9


def test_full_ai_mode_selects_all_rules(monkeypatch):
    captured = {}

    def fake_run(record, selected_rules=None):
        captured["rules"] = selected_rules

        return {
            "deal_id": record["deal_id"],
            "overall_status": "PASS",
            "summary": {
                "PASS": 11,
                "FAIL": 0,
                "NEEDS_HUMAN": 0,
            },
            "results": [],
            "rules_executed": 11,
        }

    monkeypatch.setattr(
        interactive_qc,
        "run_external_qc",
        fake_run,
    )

    sample = interactive_qc.get_sample_deals()[
        "Complete Sale"
    ]

    result = interactive_qc.run_interactive_qc(
        sample,
        mode="full_ai",
    )

    assert captured["rules"] is None
    assert result["qc"]["rules_executed"] == 11


def test_invalid_mode_rejected():
    sample = interactive_qc.get_sample_deals()[
        "Complete Sale"
    ]

    with pytest.raises(ValueError, match="Unsupported"):
        interactive_qc.run_interactive_qc(
            sample,
            mode="invalid",
        )


def test_qc_engine_error_rejected(monkeypatch):
    monkeypatch.setattr(
        interactive_qc,
        "run_external_qc",
        lambda record, selected_rules=None: {
            "error": "Invalid deal"
        },
    )

    sample = interactive_qc.get_sample_deals()[
        "Complete Sale"
    ]

    with pytest.raises(ValueError, match="Invalid deal"):
        interactive_qc.run_interactive_qc(sample)


def test_invalid_qc_response_rejected(monkeypatch):
    monkeypatch.setattr(
        interactive_qc,
        "run_external_qc",
        lambda record, selected_rules=None: None,
    )

    sample = interactive_qc.get_sample_deals()[
        "Complete Sale"
    ]

    with pytest.raises(ValueError, match="Invalid QC"):
        interactive_qc.run_interactive_qc(sample)


def test_input_not_mutated(monkeypatch):
    monkeypatch.setattr(
        interactive_qc,
        "run_external_qc",
        lambda record, selected_rules=None: {
            "overall_status": "PASS"
        },
    )

    sample = interactive_qc.get_sample_deals()[
        "Complete Sale"
    ]

    original = deepcopy(sample)

    interactive_qc.run_interactive_qc(sample)

    assert sample == original
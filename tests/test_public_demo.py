import pytest

from backend.demo_config import (
    is_public_demo,
    allow_full_ai,
)
from backend.interactive_qc import (
    get_sample_deals,
    run_interactive_qc,
)


def test_public_demo_disabled_by_default(monkeypatch):
    monkeypatch.delenv(
        "SOLARQC_PUBLIC_DEMO",
        raising=False,
    )

    assert is_public_demo() is False
    assert allow_full_ai() is True


def test_public_demo_enabled(monkeypatch):
    monkeypatch.setenv(
        "SOLARQC_PUBLIC_DEMO",
        "true",
    )

    assert is_public_demo() is True
    assert allow_full_ai() is False


def test_public_demo_accepts_numeric_true(monkeypatch):
    monkeypatch.setenv(
        "SOLARQC_PUBLIC_DEMO",
        "1",
    )

    assert is_public_demo() is True


def test_public_demo_rejects_full_ai(monkeypatch):
    monkeypatch.setenv(
        "SOLARQC_PUBLIC_DEMO",
        "true",
    )

    sample = get_sample_deals()["Complete Sale"]

    with pytest.raises(
        ValueError,
        match="unavailable",
    ):
        run_interactive_qc(
            sample,
            mode="full_ai",
        )


def test_public_demo_deterministic_execution(monkeypatch):
    monkeypatch.setenv(
        "SOLARQC_PUBLIC_DEMO",
        "true",
    )

    sample = get_sample_deals()["Complete Sale"]

    result = run_interactive_qc(
        sample,
        mode="deterministic",
    )

    assert result["mode"] == "deterministic"
    assert result["qc"]["rules_executed"] == 9
    assert result["qc"]["overall_status"] == "PASS"
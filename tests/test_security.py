from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.security import require_api_key


# ============================================================
# PROTECTED ENDPOINTS
# ============================================================

PROTECTED_ENDPOINTS = [
    ("GET", "/integrations/google-sheets"),
    ("GET", "/integrations/hubspot"),
    ("POST", "/integrations/google-sheets/qc"),
    ("POST", "/integrations/hubspot/qc"),
]


# ============================================================
# TEST ISOLATION
# ============================================================

@pytest.fixture(autouse=True)
def isolate_authentication():
    original = dict(app.dependency_overrides)

    app.dependency_overrides.pop(
        require_api_key,
        None,
    )

    yield

    app.dependency_overrides.clear()
    app.dependency_overrides.update(original)


# ============================================================
# TEST 1: MISSING API KEY
# ============================================================

@pytest.mark.parametrize("method,path", PROTECTED_ENDPOINTS)
def test_missing_api_key(method, path, monkeypatch):
    monkeypatch.setenv(
        "SOLARQC_API_KEY",
        "correct-test-key",
    )

    with TestClient(app) as client:
        response = client.request(
            method,
            path,
        )

    assert response.status_code == 401

    assert response.json()["detail"] == (
        "Invalid or missing API key."
    )


# ============================================================
# TEST 2: INCORRECT API KEY
# ============================================================

@pytest.mark.parametrize("method,path", PROTECTED_ENDPOINTS)
def test_invalid_api_key(method, path, monkeypatch):
    monkeypatch.setenv(
        "SOLARQC_API_KEY",
        "correct-test-key",
    )

    with TestClient(app) as client:
        response = client.request(
            method,
            path,
            headers={
                "X-API-Key": "wrong-key",
            },
        )

    assert response.status_code == 401


# ============================================================
# TEST 3: MISSING SERVER CONFIGURATION
# ============================================================

@pytest.mark.parametrize("method,path", PROTECTED_ENDPOINTS)
def test_missing_server_configuration(
    method,
    path,
    monkeypatch,
):
    monkeypatch.delenv(
        "SOLARQC_API_KEY",
        raising=False,
    )

    with TestClient(app) as client:
        response = client.request(
            method,
            path,
            headers={
                "X-API-Key": "some-key",
            },
        )

    assert response.status_code == 503

    assert response.json()["detail"] == (
        "API authentication is not configured."
    )


# ============================================================
# TEST 4: VALID API KEY
# ============================================================

def test_valid_api_key_reaches_hubspot_endpoint(monkeypatch):
    monkeypatch.setenv(
        "SOLARQC_API_KEY",
        "correct-test-key",
    )

    qc_result = {
        "deal_id": "DEMO-004",
        "overall_status": "PASS",
    }

    with patch(
        "backend.main.run_hubspot_qc",
        return_value=qc_result,
    ):
        with TestClient(app) as client:
            response = client.post(
                "/integrations/hubspot/qc",
                params={
                    "deal_id": "DEMO-004",
                },
                headers={
                    "X-API-Key": "correct-test-key",
                },
            )

    assert response.status_code == 200

    assert response.json()["qc"]["overall_status"] == "PASS"
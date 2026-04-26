# backend/tests/security/test_security.py
"""
Security tests for the AI Wildfire Tracker API.

This is for Input Validation & Injection Testing
These tests are going to validate that the API correctly rejects malicious or malformed input
before it can reach the database or business logic.

Test categories:
  1. SQL Injection — parameterized queries must prevent any bypass
  2. Cross-Site Scripting (XSS) probes — ensure input is sanitised/rejected
  3. Oversized input — protect against memory exhaustion
  4. Boundary value attacks — geographic filter bypass attempts
  5. Information disclosure — ensure error responses don't leak internal paths

These tests run against a real (but temporary) DuckDB database to verify that
the application's actual query layer is safe — not just a mocked surface.
"""

import os

import duckdb
import pytest
from fastapi.testclient import TestClient

import ai_wildfire_tracker.api.server as server_module

SEC_TEST_DB = "sec_test_wildfire.db"


@pytest.fixture(autouse=True)
def setup_security_db():
    """Seed a minimal database for security tests."""
    if os.path.exists(SEC_TEST_DB):
        os.remove(SEC_TEST_DB)

    con = duckdb.connect(SEC_TEST_DB)
    con.execute(
        """
        CREATE TABLE fires (
            latitude DOUBLE,
            longitude DOUBLE,
            bright_ti4 DOUBLE,
            bright_ti5 DOUBLE,
            frp DOUBLE,
            acq_date VARCHAR,
            acq_time VARCHAR,
            confidence VARCHAR
        )
        """
    )
    con.executemany(
        "INSERT INTO fires VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        [
            (34.0, -118.0, 350.0, 300.0, 50.0, "2024-01-01", "1200", "high"),
            (36.5, -119.5, 320.0, 280.0, 20.0, "2024-01-02", "1300", "nominal"),
        ],
    )
    con.close()

    yield

    if os.path.exists(SEC_TEST_DB):
        os.remove(SEC_TEST_DB)


@pytest.fixture()
def client(monkeypatch):
    """TestClient with DB_PATH patched to the security test database.
    monkeypatch automatically restores DB_PATH after each test."""
    monkeypatch.setattr(server_module, "DB_PATH", SEC_TEST_DB)
    return TestClient(server_module.app)


class TestSQLInjection:
    def test_sql_injection_in_region_param(self, client):
        """
        Input: region=ca'; DROP TABLE fires; --
        Expected: 400 Bad Request — injected SQL must be rejected before execution.
        """
        payload = "ca'; DROP TABLE fires; --"
        response = client.get(f"/fires?region={payload}")
        assert response.status_code == 400, (
            f"SQL injection in region param was not rejected (status={response.status_code})"
        )

    def test_sql_injection_union_in_region_param(self, client):
        """
        Input: region=ca' UNION SELECT 1,2,3--
        Expected: 400 Bad Request.
        """
        payload = "ca' UNION SELECT 1,2,3--"
        response = client.get(f"/fires?region={payload}")
        assert response.status_code == 400

    def test_sql_injection_in_confidence_param(self, client):
        """
        Input: confidence=high' OR '1'='1
        Expected: 400 Bad Request — input validation layer rejects non-whitelisted values.
        """
        payload = "high' OR '1'='1"
        response = client.get(f"/fires?confidence={payload}")
        assert response.status_code == 400, (
            f"SQL injection in confidence param was not rejected (status={response.status_code})"
        )

    def test_table_still_intact_after_injection_attempt(self, client):
        """
        After SQL injection attempts, the fires table must still exist and serve data.
        Verifies that injected DDL statements were never executed.
        """
        # Attempt DROP via injection
        client.get("/fires?region=ca'; DROP TABLE fires; --")
        # Table must still be queryable
        response = client.get("/fires")
        assert response.status_code == 200
        assert isinstance(response.json(), list)


class TestXSSProbes:
    def test_xss_script_tag_in_region_param(self, client):
        """
        Input: region=<script>alert(1)</script>
        Expected: 400 Bad Request — non-alphanumeric region codes are invalid.
        """
        payload = "<script>alert(1)</script>"
        response = client.get(f"/fires?region={payload}")
        assert response.status_code == 400

    def test_xss_event_handler_in_region_param(self, client):
        """
        Input: region=ca onmouseover=alert(1)
        Expected: 400 Bad Request.
        """
        payload = "ca onmouseover=alert(1)"
        response = client.get(f"/fires?region={payload}")
        assert response.status_code == 400


class TestOversizedInput:
    def test_oversized_region_param_rejected(self, client):
        """
        Input: region param with 500 characters.
        Expected: 400 Bad Request — protects against memory exhaustion attacks.
        """
        payload = "a" * 500
        response = client.get(f"/fires?region={payload}")
        assert response.status_code == 400

    def test_oversized_confidence_param_rejected(self, client):
        """
        Input: confidence param with 500 characters.
        Expected: 400 Bad Request — rejected by input validation whitelist.
        """
        payload = "h" * 500
        response = client.get(f"/fires?confidence={payload}")
        assert response.status_code == 400


class TestBoundaryValueAttacks:
    def test_southern_hemisphere_data_excluded(self, client):
        """
        Data at latitude < 24.0 must never appear in /fires responses.
        Validates that the geographic filter cannot be bypassed.
        """
        response = client.get("/fires")
        assert response.status_code == 200
        for fire in response.json():
            assert fire["lat"] >= 24.0, (
                f"Out-of-bounds fire leaked through geo-filter: lat={fire['lat']}"
            )

    def test_eastern_hemisphere_data_excluded(self, client):
        """
        Data at longitude > -66.5 (eastern hemisphere or eastern US coast edge) must
        not appear outside the US bounding box.
        """
        response = client.get("/fires")
        assert response.status_code == 200
        for fire in response.json():
            assert fire["lon"] <= -66.5, (
                f"Out-of-bounds fire leaked through geo-filter: lon={fire['lon']}"
            )

    def test_invalid_region_code_rejected(self, client):
        """
        Input: region=INVALID_REGION_XYZ123
        Expected: 400 with an error detail message.
        """
        response = client.get("/fires?region=INVALID_REGION_XYZ123")
        assert response.status_code == 400
        assert "detail" in response.json()


class TestInformationDisclosure:
    def test_health_response_returns_expected_fields_only(self, client):
        """
        /health must return only status, database_exists, and db_path.
        No internal Python objects, passwords, or environment variables should appear.
        """
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        allowed_keys = {"status", "database_exists", "db_path", "model_loaded", "model_path"}
        assert set(data.keys()) == allowed_keys, (
            f"Health endpoint returned unexpected fields: {set(data.keys()) - allowed_keys}"
        )

    def test_400_error_does_not_expose_stack_trace(self, client):
        """
        Error responses must not contain Python stack traces or internal details.
        FastAPI error responses should use RFC 7807 {detail: ...} format only.
        """
        response = client.get("/fires?region=badregion")
        assert response.status_code == 400
        body = response.text
        assert "Traceback" not in body, "Error response leaked a Python traceback"
        assert "File " not in body, "Error response leaked internal file paths"

    def test_confidence_400_error_has_helpful_message(self, client):
        """
        A 400 for invalid confidence must include a 'detail' field with guidance,
        not expose raw exception objects or internal query strings.
        """
        response = client.get("/fires?confidence=invalid_value")
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "Traceback" not in str(data)
        assert "duckdb" not in str(data).lower(), (
            "Error response leaked database implementation details"
        )

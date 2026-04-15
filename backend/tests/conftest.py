# backend/tests/conftest.py
"""
Top-level pytest configuration for backend tests.

Sets TEST_DB_PATH before any test module is collected so that the first
import of ai_wildfire_tracker.api.server picks up the correct default.
Individual test modules override this via monkeypatch or autouse fixtures.
"""

import os

# Establish a safe default so server.py doesn't bake in "wildfire.db"
# (the production default) when imported during pytest collection.
# test_api.py's autouse fixture and the new test files' monkeypatch fixtures
# each point to their own isolated database files per test.
os.environ.setdefault("TEST_DB_PATH", "test_wildfire.db")

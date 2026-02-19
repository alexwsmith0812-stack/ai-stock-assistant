"""Pytest configuration and shared fixtures."""
import os

import pytest


@pytest.fixture(autouse=True)
def mock_env_vars(monkeypatch):
    """Mock environment variables for all tests."""
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
    monkeypatch.setenv("FINNHUB_API_KEY", "test-finnhub-key")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-4o-mini")

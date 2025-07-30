"""
Pytest configuration and fixtures for Fill Rate Classifier tests.

This module provides:
- Automatic environment variable loading
- Common test fixtures
- Database setup/teardown
- Mock configurations

Dependencies: .env file in project root, src/models/ for test data
"""

import os
import pytest
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables automatically for all tests
def pytest_configure(config):
    """Load environment variables before any tests run"""
    # Find and load .env file from project root
    project_root = Path(__file__).parent.parent
    env_file = project_root / ".env"
    
    if env_file.exists():
        load_dotenv(env_file)
        print(f"✅ Loaded environment variables from {env_file}")
    else:
        print(f"⚠️  No .env file found at {env_file}")

# Ensure environment variables are available in all tests
@pytest.fixture(scope="session", autouse=True)
def load_env():
    """Automatically load environment variables for all tests"""
    # This fixture runs automatically for all tests
    # Environment variables are already loaded in pytest_configure
    pass

@pytest.fixture
def test_env_vars():
    """Provide access to test environment variables"""
    return {
        "FINCH_API_KEY": os.getenv("FINCH_API_KEY"),
        "CLAUDE_API_KEY": os.getenv("CLAUDE_API_KEY"),
        "CLAUDE_BASE_URL": os.getenv("CLAUDE_BASE_URL"),
        "API_BEARER_TOKEN": os.getenv("API_BEARER_TOKEN"),
        "HOST": os.getenv("HOST", "0.0.0.0"),
        "PORT": os.getenv("PORT", "8000"),
        "ENVIRONMENT": os.getenv("ENVIRONMENT", "test"),
        "LOG_LEVEL": os.getenv("LOG_LEVEL", "DEBUG"),
        "EMAIL_CONFIDENCE_THRESHOLD": float(os.getenv("EMAIL_CONFIDENCE_THRESHOLD", "0.7")),
        "ACTION_CONFIDENCE_THRESHOLD": float(os.getenv("ACTION_CONFIDENCE_THRESHOLD", "0.85")),
    }

@pytest.fixture
def realistic_api_responses():
    """Provide realistic API responses for testing using real data patterns"""
    return {
        "1112": {
            "company_name": "Sharon Heights Golf & Country Club",
            "tier": "Tier 3",
            "recommendation": "Fill rates are declining due to pay rates below market average. Workers are choosing higher-paying opportunities."
        },
        "2905": {
            "company_name": "Starfire Golf Club",
            "tier": "Tier 4", 
            "recommendation": "Geographic coverage is limited in rural locations. Consider expanding worker pool."
        }
    }

@pytest.fixture
def realistic_classification_data():
    """Provide realistic classification test data using real company patterns"""
    return [
        {
            "company_id": "1112",
            "api_response": "Fill rates are declining due to pay rates below market average. Workers are choosing higher-paying opportunities.",
            "expected_classification": "email",
            "confidence_threshold": 0.8
        },
        {
            "company_id": "2905",
            "api_response": "Geographic coverage is limited in rural locations. Consider expanding worker pool.",
            "expected_classification": "action",
            "confidence_threshold": 0.9
        }
    ]
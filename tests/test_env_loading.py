"""
Test environment variable loading functionality.

This test verifies that environment variables are automatically
loaded when running tests, so you don't need to manually source them.
"""

import os
import pytest


def test_env_vars_are_loaded(test_env_vars):
    """Test that environment variables are automatically loaded"""
    # These should be available from the .env file
    assert test_env_vars["FINCH_API_KEY"] is not None
    assert test_env_vars["CLAUDE_API_KEY"] is not None
    assert test_env_vars["CLAUDE_BASE_URL"] is not None
    assert test_env_vars["API_BEARER_TOKEN"] is not None
    
    # Test that we have the expected values
    assert test_env_vars["FINCH_API_KEY"] == "f1e14498dbb9b29a7abdd16fad04baa39ac29197a84f21160162516c1edcdff6"
    assert test_env_vars["CLAUDE_BASE_URL"] == "https://finch.instawork.com"
    assert test_env_vars["HOST"] == "0.0.0.0"
    assert test_env_vars["PORT"] == "8000"


def test_env_vars_direct_access():
    """Test that environment variables are available directly via os.getenv"""
    # These should be available directly from os.getenv
    assert os.getenv("FINCH_API_KEY") is not None
    assert os.getenv("CLAUDE_API_KEY") is not None
    assert os.getenv("CLAUDE_BASE_URL") is not None
    assert os.getenv("API_BEARER_TOKEN") is not None


def test_default_values(test_env_vars):
    """Test that default values are provided for missing env vars"""
    # These should have default values if not in .env
    assert test_env_vars["ENVIRONMENT"] in ["development", "test"]
    assert test_env_vars["LOG_LEVEL"] in ["INFO", "DEBUG"]
    assert isinstance(test_env_vars["EMAIL_CONFIDENCE_THRESHOLD"], float)
    assert isinstance(test_env_vars["ACTION_CONFIDENCE_THRESHOLD"], float)


def test_no_manual_source_needed():
    """Test that you don't need to manually source environment variables"""
    # This test should pass without any manual environment setup
    # The conftest.py should handle loading automatically
    
    # Verify key environment variables are available
    required_vars = [
        "FINCH_API_KEY",
        "CLAUDE_API_KEY", 
        "CLAUDE_BASE_URL",
        "API_BEARER_TOKEN"
    ]
    
    for var in required_vars:
        value = os.getenv(var)
        assert value is not None, f"Environment variable {var} should be automatically loaded"
        assert len(value) > 0, f"Environment variable {var} should not be empty"


if __name__ == "__main__":
    # You can also run this directly to test
    pytest.main([__file__, "-v"]) 
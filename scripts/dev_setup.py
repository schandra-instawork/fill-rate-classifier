#!/usr/bin/env python3
"""
Development setup script for Fill Rate Classifier.

This script automatically loads environment variables and sets up
the development environment so you don't need to manually source them.

Dependencies: .env file in project root

Usage:
    python scripts/dev_setup.py
    # or
    source <(python scripts/dev_setup.py)
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv


def load_environment():
    """Load environment variables from .env file"""
    project_root = Path(__file__).parent.parent
    env_file = project_root / ".env"
    
    if env_file.exists():
        load_dotenv(env_file)
        print(f"✅ Loaded environment variables from {env_file}")
        return True
    else:
        print(f"❌ No .env file found at {env_file}")
        return False


def verify_environment():
    """Verify that key environment variables are loaded"""
    required_vars = [
        "FINCH_API_KEY",
        "CLAUDE_API_KEY", 
        "CLAUDE_BASE_URL",
        "API_BEARER_TOKEN"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing environment variables: {missing_vars}")
        return False
    else:
        print("✅ All required environment variables are loaded")
        return True


def print_environment_summary():
    """Print a summary of the current environment"""
    print("\n📋 Environment Summary:")
    print(f"  ENVIRONMENT: {os.getenv('ENVIRONMENT', 'development')}")
    print(f"  LOG_LEVEL: {os.getenv('LOG_LEVEL', 'INFO')}")
    print(f"  HOST: {os.getenv('HOST', '0.0.0.0')}")
    print(f"  PORT: {os.getenv('PORT', '8000')}")
    print(f"  EMAIL_CONFIDENCE_THRESHOLD: {os.getenv('EMAIL_CONFIDENCE_THRESHOLD', '0.7')}")
    print(f"  ACTION_CONFIDENCE_THRESHOLD: {os.getenv('ACTION_CONFIDENCE_THRESHOLD', '0.85')}")
    
    # Check if API keys are loaded (without exposing them)
    if os.getenv("FINCH_API_KEY"):
        print(f"  FINCH_API_KEY: {'*' * 20}... (loaded)")
    if os.getenv("CLAUDE_API_KEY"):
        print(f"  CLAUDE_API_KEY: {'*' * 20}... (loaded)")
    if os.getenv("CLAUDE_BASE_URL"):
        print(f"  CLAUDE_BASE_URL: {os.getenv('CLAUDE_BASE_URL')}")


def main():
    """Main function to set up development environment"""
    print("🚀 Setting up Fill Rate Classifier development environment...")
    
    # Load environment variables
    if not load_environment():
        sys.exit(1)
    
    # Verify environment
    if not verify_environment():
        sys.exit(1)
    
    # Print summary
    print_environment_summary()
    
    print("\n✅ Development environment is ready!")
    print("💡 You can now run tests, scripts, or the application without manually sourcing environment variables.")
    
    # If called with --export, export the variables for shell use
    if "--export" in sys.argv:
        print("\n📝 Export commands for shell:")
        for key, value in os.environ.items():
            if key.startswith(("FINCH_", "CLAUDE_", "API_", "HOST", "PORT", "ENVIRONMENT", "LOG_LEVEL")):
                print(f"export {key}='{value}'")


if __name__ == "__main__":
    main() 
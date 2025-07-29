#!/bin/bash
"""
Quick start script for Fill Rate Classifier.

This script sets up everything you need for development:
- Activates virtual environment
- Installs/updates packages
- Loads environment variables
- Sets up Python path

Usage:
    source scripts/quick_start.sh
"""

# Source the main setup script
source "$(dirname "$0")/setup_env.sh"

echo ""
echo "🚀 Quick start complete! You can now:"
echo ""
echo "   # Run tests"
echo "   python -m pytest"
echo ""
echo "   # Start the API server"
echo "   python src/api/server.py"
echo ""
echo "   # Run experiments"
echo "   python scripts/run_experiment.py"
echo ""
echo "   # Check environment health"
echo "   python scripts/fix_venv.py" 
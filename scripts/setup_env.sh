#!/bin/bash
# Quick environment setup script for Fill Rate Classifier.
#
# This script loads environment variables and activates the virtual environment
# so you can start development immediately.
#
# Usage:
#     source scripts/setup_env.sh
#     # or
#     . scripts/setup_env.sh

set -e  # Exit on any error

echo "🚀 Setting up Fill Rate Classifier environment..."

# Get the project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Check if virtual environment exists
if [ ! -d "$PROJECT_ROOT/venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv "$PROJECT_ROOT/venv"
fi

# Activate virtual environment
echo "✅ Activating virtual environment..."
source "$PROJECT_ROOT/venv/bin/activate"

# Run diagnostic and fix any issues
echo "🔍 Running environment diagnostic..."
python "$PROJECT_ROOT/scripts/fix_venv.py"

# Load environment variables using Python
echo "✅ Loading environment variables..."
python "$PROJECT_ROOT/scripts/dev_setup.py"

# Set up Python path
export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"

echo ""
echo "🎉 Environment is ready!"
echo "💡 You can now run:"
echo "   - python -m pytest (run tests)"
echo "   - python src/api/server.py (start API server)"
echo "   - python scripts/run_experiment.py (run experiments)"
echo ""
echo "🔧 Current environment:"
echo "   PYTHONPATH: $PYTHONPATH"
echo "   VIRTUAL_ENV: $VIRTUAL_ENV"
echo "   ENVIRONMENT: $ENVIRONMENT"
echo "   Python: $(which python)"
echo "   Pip: $(which pip)" 
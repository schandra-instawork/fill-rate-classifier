#!/usr/bin/env python3
"""
File Structure Cleanup Script

This script reorganizes the project structure for better LLM navigation
by moving files to their proper locations.
"""

import os
import shutil
from pathlib import Path

def create_directories():
    """Create necessary directories"""
    directories = [
        "docs",
        "tests/unit", 
        "tests/integration"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created directory: {directory}")

def move_documentation_files():
    """Move documentation files to docs/ directory"""
    doc_files = [
        "README.md",
        "ISSUE_SPECIFIC_EMAIL_SYSTEM_REPORT.md",
        "STREAMLINED_STRUCTURE.md", 
        "RECOMMENDED_STRUCTURE.md",
        "COMPREHENSIVE_CURSOR_RULES_SUMMARY.md",
        "PYTHON_WEB_RULES_SUMMARY.md",
        "INTELLIGENT_RULES_SUMMARY.md",
        "CURSOR_VS_CLAUDE_RULES.md",
        "input_prompt.md"
    ]
    
    for file in doc_files:
        if os.path.exists(file):
            # Copy to docs directory
            shutil.copy2(file, f"docs/{file}")
            print(f"✅ Moved {file} to docs/")
        else:
            print(f"⚠️  File not found: {file}")

def move_test_files():
    """Move test files to tests/ directory"""
    test_files = [
        "test_simple.py",
        "test_cursor_rules_validator.py", 
        "test_intelligent_rules.py",
        "cursor_rules_validator.py",
        "cursor_validator_cli.py"
    ]
    
    for file in test_files:
        if os.path.exists(file):
            # Move to tests directory
            shutil.move(file, f"tests/{file}")
            print(f"✅ Moved {file} to tests/")
        else:
            print(f"⚠️  File not found: {file}")

def move_utility_scripts():
    """Move utility scripts to scripts/ directory"""
    utility_files = [
        "example_usage.py"
    ]
    
    for file in utility_files:
        if os.path.exists(file):
            # Move to scripts directory
            shutil.move(file, f"scripts/{file}")
            print(f"✅ Moved {file} to scripts/")
        else:
            print(f"⚠️  File not found: {file}")

def update_import_paths():
    """Update import paths in moved files"""
    # This would require more complex logic to update imports
    # For now, just note that imports need to be updated
    print("⚠️  Note: Import paths may need manual updates in moved files")

def main():
    """Main cleanup function"""
    print("🏗️  Starting File Structure Cleanup...")
    print("=" * 50)
    
    # Create directories
    create_directories()
    
    # Move documentation files
    print("\n📄 Moving documentation files...")
    move_documentation_files()
    
    # Move test files
    print("\n🧪 Moving test files...")
    move_test_files()
    
    # Move utility scripts
    print("\n🔧 Moving utility scripts...")
    move_utility_scripts()
    
    # Note about imports
    print("\n⚠️  IMPORTANT: You may need to update import paths in moved files")
    
    print("\n✅ File structure cleanup completed!")
    print("\n📁 New structure:")
    print("""
    fill-rate-classifier/
    ├── 📁 src/                          # Main source code
    ├── 📁 tests/                        # All test files
    ├── 📁 config/                       # Configuration files
    ├── 📁 data/                         # Data files
    ├── 📁 scripts/                      # Utility scripts
    ├── 📁 docs/                         # Documentation
    ├── 📁 .cursor/                      # Cursor rules
    ├── 📄 requirements.txt
    ├── 📄 setup.py
    ├── 📄 pytest.ini
    └── 📄 .env
    """)

if __name__ == "__main__":
    main() 
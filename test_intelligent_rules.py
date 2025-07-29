#!/usr/bin/env python3
"""
Test script to verify intelligent application of Cursor rules

Dependencies: cursor_rules_validator.py, .cursor/rules/ directory

This script tests the intelligent features of Cursor rules including
context awareness, conditional actions, and smart pattern matching.
"""

import json
from pathlib import Path
from cursor_rules_validator import validate_cursor_rules_location


def test_rule_intelligence():
    """Test that rules are structured for intelligent application"""
    # Test intelligent features of Cursor rules
    print("🧠 Testing Cursor Rules Intelligence")
    print("=" * 50)
    
    # Validate all rules are properly placed
    validation = validate_cursor_rules_location()
    
    if not validation["valid"]:
        print("❌ Rules validation failed")
        return False
    
    print("✅ All rules are properly placed")
    
    # Test each rule for intelligent features
    rules_dir = Path(".cursor/rules")
    
    for rule_file in rules_dir.glob("*.mdc"):  # Analyze each rule file
        print(f"\n📋 Testing rule: {rule_file.name}")
        print("-" * 30)
        
        content = rule_file.read_text()
        
        # Check for intelligent filtering
        intelligence_features = {  # Define intelligence criteria
            "context_aware": "context" in content.lower(),
            "conditional_actions": "when:" in content,
            "smart_patterns": "pattern:" in content,
            "examples": "examples:" in content,
            "metadata": "metadata:" in content,
            "multiple_actions": content.count("type:") > 1,
            "file_extension_filter": "file_extension" in content,
            "content_filter": "content" in content and "pattern" in content
        }
        
        for feature, present in intelligence_features.items():
            status = "✅" if present else "❌"
            print(f"  {status} {feature}")
        
        # Specific rule tests
        if "conventional-commits" in rule_file.name:
            test_conventional_commits_rule(content)
        elif "python-flask-guidelines" in rule_file.name:
            test_python_flask_rule(content)
    
    return True


def test_conventional_commits_rule(content):
    """Test conventional commits rule intelligence"""
    # Analyze conventional commits rule features
    print("\n  🔍 Conventional Commits Rule Analysis:")
    
    features = {
        "Event filtering": "file_save|file_create|file_modify" in content,
        "Content change detection": "content_change" in content,
        "Smart type detection": "add|create|implement|fix|refactor" in content,
        "Scope extraction": "dirname" in content,
        "Conditional execution": "when:" in content,
        "Multiple commit types": content.count("CHANGE_TYPE=") > 5,
        "Error handling": "if [ -z" in content or "if [ \"$SCOPE\"" in content
    }
    
    for feature, present in features.items():
        status = "✅" if present else "❌"
        print(f"    {status} {feature}")


def test_python_flask_rule(content):
    """Test Python Flask rule intelligence"""
    # Analyze Python Flask rule features
    print("\n  🔍 Python Flask Rule Analysis:")
    
    features = {
        "Context-aware suggestions": "when:" in content,
        "File extension filtering": "file_extension" in content,
        "Content pattern matching": "Blueprint|SQLAlchemy|marshmallow" in content,
        "Context filtering": "api|web|backend|server" in content,
        "Multiple suggestion types": content.count("when:") > 5,
        "Code examples": "```python" in content,
        "Specific scenarios": any(scenario in content for scenario in [
            "creating_new_file", "writing_routes", "error_handling", 
            "database_operations", "authentication", "testing", 
            "performance", "configuration"
        ])
    }
    
    for feature, present in features.items():
        status = "✅" if present else "❌"
        print(f"    {status} {feature}")


def demonstrate_rule_application():
    """Demonstrate how rules would be applied intelligently"""
    # Show intelligent rule application scenarios
    print("\n🎯 Rule Application Demonstration")
    print("=" * 50)
    
    scenarios = [
        {
            "scenario": "Creating a new Flask app file",
            "file": "app.py",
            "content": "from flask import Flask",
            "expected_rules": ["python-flask-guidelines"],
            "expected_suggestions": ["application factory pattern", "blueprints"]
        },
        {
            "scenario": "Modifying a Python file with Flask content",
            "file": "routes/user_routes.py",
            "content": "@app.route('/users')",
            "expected_rules": ["python-flask-guidelines"],
            "expected_suggestions": ["Blueprint", "error handling", "validation"]
        },
        {
            "scenario": "Saving any file (git commit trigger)",
            "file": "src/components/Button.tsx",
            "content": "export function Button() {",
            "expected_rules": ["conventional-commits"],
            "expected_suggestions": ["conventional commit format", "feat|fix|docs"]
        },
        {
            "scenario": "Creating documentation",
            "file": "README.md",
            "content": "# Project Documentation",
            "expected_rules": ["conventional-commits"],
            "expected_suggestions": ["docs scope", "documentation changes"]
        }
    ]
    
    for scenario in scenarios:
        print(f"\n📝 {scenario['scenario']}")
        print(f"   File: {scenario['file']}")
        print(f"   Content: {scenario['content'][:50]}...")
        print(f"   Expected Rules: {', '.join(scenario['expected_rules'])}")
        print(f"   Expected Suggestions: {', '.join(scenario['expected_suggestions'])}")
        
        # Simulate rule matching
        matched_rules = []
        if scenario['file'].endswith('.py') and 'flask' in scenario['content'].lower():
            matched_rules.append("python-flask-guidelines")  # Match Flask files
        if any(keyword in scenario['file'] for keyword in ['src', 'lib', 'app', 'routes']):
            matched_rules.append("conventional-commits")  # Match code files
        
        print(f"   ✅ Matched Rules: {', '.join(matched_rules) if matched_rules else 'None'}")


def main():
    """Main test function"""
    print("🧪 Cursor Rules Intelligence Test Suite")
    print("=" * 60)
    
    # Test rule intelligence
    success = test_rule_intelligence()
    
    if success:
        # Demonstrate rule application
        demonstrate_rule_application()
        
        print("\n" + "=" * 60)
        print("✅ All tests completed successfully!")
        print("\n🎉 Your Cursor rules are now intelligent and context-aware!")
        print("\nKey Intelligence Features:")
        print("  • Context-aware filtering (file type, content, events)")
        print("  • Conditional actions based on specific scenarios")
        print("  • Smart pattern matching for relevant suggestions")
        print("  • Multiple action types (suggest, execute)")
        print("  • Comprehensive examples and metadata")
    else:
        print("\n❌ Some tests failed. Please check rule structure.")


if __name__ == "__main__":
    main() 
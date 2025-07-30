#!/usr/bin/env python3
"""
Module: scripts.example_usage
Purpose: Example usage of the Cursor Rules Validator
Dependencies: tests.cursor_rules_validator

This script demonstrates how to use the cursor_rules_validator functions
to validate and manage Cursor rule files in your project.
"""

import sys
from pathlib import Path

# Add the tests directory to the path so we can import the validator
sys.path.insert(0, str(Path(__file__).parent.parent / "tests"))

from cursor_rules_validator import (
    validate_cursor_rules_location,
    validate_all_rules,
    generate_validation_report
)


def demonstrate_basic_validation():
    """Demonstrate basic validation functionality"""
    print("🔍 Basic Validation Demo")
    print("=" * 30)
    
    # Validate rule locations
    location_result = validate_cursor_rules_location()
    print(f"Location validation: {'✅ PASSED' if location_result['valid'] else '❌ FAILED'}")
    
    if not location_result['valid']:
        print("Issues found:")
        for error in location_result['errors']:
            print(f"  - {error}")
    
    # Validate rule structure
    structure_result = validate_all_rules()
    print(f"Structure validation: {'✅ PASSED' if structure_result.get('valid', False) else '❌ FAILED'}")
    
    if structure_result.get('file_details'):
        print("File details:")
        for file_name, details in structure_result['file_details'].items():
            status = "✅" if details['valid'] else "❌"
            print(f"  {status} {file_name}")


def demonstrate_detailed_report():
    """Demonstrate detailed report generation"""
    print("\n📄 Detailed Report Demo")
    print("=" * 30)
    
    report = generate_validation_report()
    print(report)


def demonstrate_file_management():
    """Demonstrate file management functionality"""
    print("\n📁 File Management Demo")
    print("=" * 30)
    
    # Example: Check for misplaced files
    project_root = Path(".")
    mdc_files = list(project_root.rglob("*.mdc"))
    
    print(f"Found {len(mdc_files)} .mdc files in project:")
    for mdc_file in mdc_files:
        if ".cursor/rules" in str(mdc_file):
            print(f"  ✅ {mdc_file} (correct location)")
        else:
            print(f"  ❌ {mdc_file} (wrong location)")
            print(f"     Should be moved to .cursor/rules/")


def demonstrate_rule_analysis():
    """Demonstrate rule analysis functionality"""
    print("\n🔍 Rule Analysis Demo")
    print("=" * 30)
    
    cursor_rules_dir = Path(".cursor/rules")
    if cursor_rules_dir.exists():
        mdc_files = list(cursor_rules_dir.glob("*.mdc"))
        print(f"Found {len(mdc_files)} Cursor rule files:")
        
        for mdc_file in mdc_files:
            print(f"\n📝 {mdc_file.name}:")
            
            # Analyze file content
            content = mdc_file.read_text()
            
            # Check for key elements
            has_name = 'name:' in content
            has_description = 'description:' in content
            has_filters = 'filters:' in content
            has_actions = 'actions:' in content
            has_examples = 'examples:' in content
            
            print(f"  ✅ Name: {has_name}")
            print(f"  ✅ Description: {has_description}")
            print(f"  ✅ Filters: {has_filters}")
            print(f"  ✅ Actions: {has_actions}")
            print(f"  ✅ Examples: {has_examples}")
            
            # Count lines
            line_count = len(content.split('\n'))
            print(f"  📊 Lines: {line_count}")
    else:
        print("❌ .cursor/rules directory not found")


def demonstrate_error_handling():
    """Demonstrate error handling scenarios"""
    print("\n⚠️  Error Handling Demo")
    print("=" * 30)
    
    # Test with non-existent directory
    print("Testing with non-existent directory:")
    result = validate_cursor_rules_location("non_existent_dir")
    print(f"Result: {'❌ FAILED' if not result['valid'] else '✅ PASSED'}")
    
    if not result['valid']:
        for error in result['errors']:
            print(f"  - {error}")


def demonstrate_suggestions():
    """Demonstrate suggestion generation"""
    print("\n💡 Suggestions Demo")
    print("=" * 30)
    
    # Get validation results
    location_result = validate_cursor_rules_location()
    structure_result = validate_all_rules()
    
    # Collect all suggestions
    all_suggestions = []
    
    if location_result['suggestions']:
        all_suggestions.extend(location_result['suggestions'])
    
    if structure_result.get('file_details'):
        for file_name, details in structure_result['file_details'].items():
            if details['suggestions']:
                all_suggestions.extend([f"{file_name}: {s}" for s in details['suggestions']])
    
    if all_suggestions:
        print("Suggestions for improvement:")
        for i, suggestion in enumerate(all_suggestions, 1):
            print(f"  {i}. {suggestion}")
    else:
        print("✅ No suggestions needed - everything looks good!")


def main():
    """Main demonstration function"""
    print("🚀 Cursor Rules Validator - Example Usage")
    print("=" * 50)
    
    try:
        # Run all demonstrations
        demonstrate_basic_validation()
        demonstrate_detailed_report()
        demonstrate_file_management()
        demonstrate_rule_analysis()
        demonstrate_error_handling()
        demonstrate_suggestions()
        
        print("\n" + "=" * 50)
        print("✅ All demonstrations completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error during demonstration: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main()) 
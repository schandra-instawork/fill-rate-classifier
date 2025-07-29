#!/usr/bin/env python3
"""
Example usage of the Cursor Rules Validator

This script demonstrates how to use the cursor_rules_validator functions
to validate and manage Cursor rule files in your project.

Dependencies: cursor_rules_validator.py, .cursor/rules/ directory
"""

from cursor_rules_validator import (
    validate_cursor_rules_location,
    create_cursor_rules_directory,
    move_cursor_rule_file,
    get_cursor_rules_summary
)
from pathlib import Path


def main():
    """Main example function demonstrating the validator usage"""
    # Demonstrate comprehensive validator functionality
    print("Cursor Rules Validator - Example Usage")
    print("=" * 50)
    
    # Example 1: Check current project state
    print("\n1. Checking current project state:")
    print("-" * 30)
    summary = get_cursor_rules_summary()  # Get initial validation state
    print(summary)
    
    # Example 2: Create the .cursor/rules directory
    print("\n2. Creating .cursor/rules directory:")
    print("-" * 30)
    if create_cursor_rules_directory():
        print("✅ Successfully created .cursor/rules directory structure")
    else:
        print("❌ Failed to create directory structure")
    
    # Example 3: Create a sample rule file in wrong location
    print("\n3. Creating a sample rule file in wrong location:")
    print("-" * 30)
    sample_rule_content = """  # Sample Cursor rule content for testing
---
description: Sample Cursor Rule
globs: *.py
---
# Sample Rule

<rule>
name: sample_rule
description: This is a sample Cursor rule
filters:
  - type: file_extension
    pattern: "\\.py$"
actions:
  - type: suggest
    message: "This is a Python file"
</rule>
"""
    
    # Create a file in the wrong location
    wrong_location_file = Path("sample-rule.mdc")
    wrong_location_file.write_text(sample_rule_content)  # Create file in wrong location
    print(f"📄 Created sample rule file at: {wrong_location_file}")
    
    # Example 4: Validate again to see the error
    print("\n4. Validating after creating file in wrong location:")
    print("-" * 30)
    validation_result = validate_cursor_rules_location()
    print(f"Valid: {validation_result['valid']}")
    print(f"Errors: {len(validation_result['errors'])}")
    print(f"Warnings: {len(validation_result['warnings'])}")
    
    if validation_result['errors']:
        print("\nErrors found:")
        for error in validation_result['errors']:
            print(f"  {error}")
    
    # Example 5: Move the file to correct location
    print("\n5. Moving file to correct location:")
    print("-" * 30)
    success, message = move_cursor_rule_file("sample-rule.mdc")  # Move to correct location
    if success:
        print(f"✅ {message}")
    else:
        print(f"❌ {message}")
    
    # Example 6: Final validation
    print("\n6. Final validation after moving file:")
    print("-" * 30)
    final_summary = get_cursor_rules_summary()
    print(final_summary)
    
    # Example 7: Demonstrate moving a file with special characters
    print("\n7. Demonstrating kebab-case conversion:")
    print("-" * 30)
    special_char_file = Path("My Special Rule File!.mdc")
    special_char_file.write_text("<rule>test</rule>")  # Create file with special characters
    print(f"📄 Created file with special characters: {special_char_file}")
    
    success, message = move_cursor_rule_file(str(special_char_file))
    if success:
        print(f"✅ {message}")
        print("Note: Filename was converted to kebab-case")
    
    # Example 8: Show final project structure
    print("\n8. Final project structure:")
    print("-" * 30)
    cursor_rules_dir = Path(".cursor/rules")
    if cursor_rules_dir.exists():  # Display organized rule files
        print("📁 .cursor/rules/ directory contains:")
        for file in cursor_rules_dir.glob("*.mdc"):
            print(f"  📄 {file.name}")
    
    print("\n" + "=" * 50)
    print("Example completed successfully!")
    print("Your Cursor rules are now properly organized.")


if __name__ == "__main__":
    main() 
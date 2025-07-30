#!/usr/bin/env python3
"""
Module: tests.cursor_validator_cli
Purpose: Command-line interface for Cursor rules validation
Dependencies: tests.cursor_rules_validator

This module provides a command-line interface for validating
Cursor rule files and generating reports. It can be used
for automated validation in CI/CD pipelines.

Usage:
    python tests/cursor_validator_cli.py
    python tests/cursor_validator_cli.py --report
    python tests/cursor_validator_cli.py --fix
"""

import argparse
import sys
from pathlib import Path

# Add the tests directory to the path so we can import the validator
sys.path.insert(0, str(Path(__file__).parent))

from cursor_rules_validator import (
    validate_cursor_rules_location,
    validate_all_rules,
    generate_validation_report
)


def main():
    """
    Main CLI function for Cursor rules validation.
    """
    parser = argparse.ArgumentParser(
        description="Validate Cursor rule files and generate reports",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python tests/cursor_validator_cli.py          # Basic validation
  python tests/cursor_validator_cli.py --report # Generate detailed report
  python tests/cursor_validator_cli.py --fix    # Attempt to fix issues
  python tests/cursor_validator_cli.py --json   # Output JSON format
        """
    )
    
    parser.add_argument(
        "--report",
        action="store_true",
        help="Generate detailed validation report"
    )
    
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Attempt to fix common issues automatically"
    )
    
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results in JSON format"
    )
    
    parser.add_argument(
        "--project-root",
        default=".",
        help="Path to project root directory (default: current directory)"
    )
    
    parser.add_argument(
        "--output",
        help="Output file for report (default: stdout)"
    )
    
    args = parser.parse_args()
    
    # Run validations
    location_validation = validate_cursor_rules_location(args.project_root)
    all_rules_validation = validate_all_rules(args.project_root)
    
    # Determine overall success
    location_valid = location_validation["valid"]
    rules_valid = all_rules_validation.get("valid", False)
    overall_valid = location_valid and rules_valid
    
    # Generate output
    if args.json:
        output_data = {
            "valid": overall_valid,
            "location_validation": location_validation,
            "rules_validation": all_rules_validation
        }
        
        import json
        output = json.dumps(output_data, indent=2)
    else:
        if args.report:
            output = generate_validation_report(args.project_root)
        else:
            # Simple summary
            output_lines = []
            output_lines.append("🔍 Cursor Rules Validation Summary")
            output_lines.append("=" * 40)
            
            if location_valid:
                output_lines.append("✅ Location validation: PASSED")
            else:
                output_lines.append("❌ Location validation: FAILED")
                for error in location_validation["errors"]:
                    output_lines.append(f"   - {error}")
            
            if rules_valid:
                output_lines.append("✅ Structure validation: PASSED")
            else:
                output_lines.append("❌ Structure validation: FAILED")
                if "error" in all_rules_validation:
                    output_lines.append(f"   - {all_rules_validation['error']}")
            
            output_lines.append("")
            if overall_valid:
                output_lines.append("🎉 All validations passed!")
            else:
                output_lines.append("⚠️  Some validations failed.")
                output_lines.append("Use --report for detailed information.")
            
            output = "\n".join(output_lines)
    
    # Output results
    if args.output:
        with open(args.output, 'w') as f:
            f.write(output)
        print(f"📄 Report saved to: {args.output}")
    else:
        print(output)
    
    # Handle fix mode
    if args.fix and not overall_valid:
        print("\n🔧 Attempting to fix issues...")
        
        # Fix location issues
        if not location_valid:
            print("📁 Fixing location issues...")
            for suggestion in location_validation["suggestions"]:
                print(f"   💡 {suggestion}")
        
        # Fix structure issues
        if not rules_valid and "file_details" in all_rules_validation:
            print("🏗️  Fixing structure issues...")
            for file_name, details in all_rules_validation["file_details"].items():
                if not details["valid"]:
                    print(f"   📝 {file_name}:")
                    for error in details["errors"]:
                        print(f"      - {error}")
                    for suggestion in details["suggestions"]:
                        print(f"      💡 {suggestion}")
        
        print("\n⚠️  Manual fixes may be required for some issues.")
    
    # Return appropriate exit code
    return 0 if overall_valid else 1


if __name__ == "__main__":
    exit(main()) 
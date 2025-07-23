#!/usr/bin/env python3
"""
Command-line interface for the Cursor Rules Validator

Usage:
    python3 cursor_validator_cli.py [command] [options]

Commands:
    validate    - Validate Cursor rule file locations
    move        - Move a file to the correct location
    create-dir  - Create the .cursor/rules directory
    summary     - Show validation summary
    help        - Show this help message
"""

import sys
import argparse
from pathlib import Path
from cursor_rules_validator import (
    validate_cursor_rules_location,
    create_cursor_rules_directory,
    move_cursor_rule_file,
    get_cursor_rules_summary
)

# Command-line interface for Cursor rules validation


def main():
    """Main CLI function"""
    # Parse command line arguments for rule validation
    parser = argparse.ArgumentParser(
        description="Cursor Rules Validator - Validate and manage Cursor rule files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 cursor_validator_cli.py validate
  python3 cursor_validator_cli.py move my-rule.mdc
  python3 cursor_validator_cli.py create-dir
  python3 cursor_validator_cli.py summary
        """
    )
    
    parser.add_argument(
        'command',
        choices=['validate', 'move', 'create-dir', 'summary', 'help'],
        help='Command to execute'
    )
    
    parser.add_argument(
        'file_path',
        nargs='?',
        help='File path (required for move command)'
    )
    
    parser.add_argument(
        '--project-root',
        default='.',
        help='Project root directory (default: current directory)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Verbose output'
    )
    
    args = parser.parse_args()
    
    if args.command == 'help':
        parser.print_help()
        return
    
    try:
        if args.command == 'validate':
            validate_command(args)
        elif args.command == 'move':
            move_command(args)
        elif args.command == 'create-dir':
            create_dir_command(args)
        elif args.command == 'summary':
            summary_command(args)
    
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


def validate_command(args):
    """Handle validate command"""
    # Validate rule file locations and display results
    print("🔍 Validating Cursor rule file locations...")
    result = validate_cursor_rules_location(args.project_root)
    
    if result["valid"]:
        print("✅ All Cursor rule files are correctly placed!")
    else:
        print("❌ Found issues with Cursor rule file placement:")
        for error in result["errors"]:
            print(f"  {error}")
    
    if args.verbose:
        print(f"\n📊 Validation Details:")
        print(f"  Valid files: {len(result['valid_files'])}")
        print(f"  Invalid files: {len(result['invalid_files'])}")
        print(f"  Warnings: {len(result['warnings'])}")
        
        if result["valid_files"]:
            print(f"\n✅ Correctly placed files:")
            for file in result["valid_files"]:
                print(f"  {file}")
        
        if result["warnings"]:
            print(f"\n⚠️  Warnings:")
            for warning in result["warnings"]:
                print(f"  {warning}")
        
        if result["suggestions"]:
            print(f"\n💡 Suggestions:")
            for suggestion in result["suggestions"]:
                print(f"  {suggestion}")


def move_command(args):
    """Handle move command"""
    # Move file to correct .cursor/rules location
    if not args.file_path:
        print("❌ Error: File path is required for move command")
        print("Usage: python3 cursor_validator_cli.py move <file_path>")
        sys.exit(1)
    
    print(f"📦 Moving {args.file_path} to correct location...")
    success, message = move_cursor_rule_file(args.file_path, args.project_root)
    
    if success:
        print(f"✅ {message}")
    else:
        print(f"❌ {message}")
        sys.exit(1)


def create_dir_command(args):
    """Handle create-dir command"""
    # Create required directory structure for rules
    print("📁 Creating .cursor/rules directory structure...")
    success = create_cursor_rules_directory(args.project_root)
    
    if success:
        print("✅ Directory structure created successfully")
        
        if args.verbose:
            cursor_rules_dir = Path(args.project_root) / ".cursor" / "rules"
            print(f"📂 Created directory: {cursor_rules_dir.absolute()}")
    else:
        print("❌ Failed to create directory structure")
        sys.exit(1)


def summary_command(args):
    """Handle summary command"""
    # Display formatted validation summary
    print("📋 Cursor Rules Validation Summary")
    print("=" * 40)
    summary = get_cursor_rules_summary(args.project_root)
    print(summary)


if __name__ == "__main__":
    main() 
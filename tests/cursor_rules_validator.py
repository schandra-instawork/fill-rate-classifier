#!/usr/bin/env python3
"""
Module: tests.cursor_rules_validator
Purpose: Validates Cursor rule files and ensures proper structure
Dependencies: .cursor/rules/ directory structure

This module provides comprehensive validation for Cursor rule files,
ensuring they follow proper formatting, structure, and best practices.
It checks for common issues and provides suggestions for improvement.

Usage:
    python tests/cursor_rules_validator.py
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass


@dataclass
class ValidationResult:
    """Result of validation check"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    suggestions: List[str]


def validate_cursor_rules_location(project_root: str = ".") -> Dict[str, any]:
    # Validates .mdc files are in correct .cursor/rules directory
    """
    Validates that Cursor rule files (.mdc) are placed in the correct directory structure.
    
    Args:
        project_root: Path to the project root directory (default: current directory)
        
    Returns:
        Dictionary containing validation results with the following structure:
        {
            "valid": bool,
            "errors": List[str],
            "warnings": List[str],
            "valid_files": List[str],
            "invalid_files": List[str],
            "suggestions": List[str]
        }
    """
    cursor_rules_dir = Path(project_root) / ".cursor" / "rules"
    valid_files = []
    invalid_files = []
    errors = []
    warnings = []
    suggestions = []
    
    # Check if .cursor/rules directory exists
    if not cursor_rules_dir.exists():
        errors.append(f"Cursor rules directory not found: {cursor_rules_dir}")
        return {
            "valid": False,
            "errors": errors,
            "warnings": warnings,
            "valid_files": valid_files,
            "invalid_files": invalid_files,
            "suggestions": suggestions
        }
    
    # Find all .mdc files in the project
    mdc_files = list(Path(project_root).rglob("*.mdc"))
    
    for mdc_file in mdc_files:
        # Check if file is in the correct location
        if cursor_rules_dir in mdc_file.parents:
            valid_files.append(str(mdc_file))
        else:
            invalid_files.append(str(mdc_file))
            errors.append(f"Cursor rule file in wrong location: {mdc_file}")
            suggestions.append(f"Move {mdc_file} to {cursor_rules_dir}")
    
    # Check for common issues
    for mdc_file in valid_files:
        file_path = Path(mdc_file)
        if file_path.exists():
            content = file_path.read_text()
            
            # Check for basic structure
            if not content.strip():
                warnings.append(f"Empty file: {mdc_file}")
            
            # Check for rule structure
            if "<rule>" not in content:
                warnings.append(f"Missing <rule> tag in: {mdc_file}")
            
            # Check for name attribute
            if 'name:' not in content:
                warnings.append(f"Missing rule name in: {mdc_file}")
    
    return {
        "valid": len(invalid_files) == 0,
        "errors": errors,
        "warnings": warnings,
        "valid_files": valid_files,
        "invalid_files": invalid_files,
        "suggestions": suggestions
    }


def validate_rule_structure(file_path: str) -> ValidationResult:
    """
    Validates the structure of a single Cursor rule file.
    
    Args:
        file_path: Path to the .mdc file to validate
        
    Returns:
        ValidationResult with validation details
    """
    errors = []
    warnings = []
    suggestions = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return ValidationResult(
            is_valid=False,
            errors=[f"Cannot read file: {e}"],
            warnings=warnings,
            suggestions=suggestions
        )
    
    # Check for required elements
    if not content.strip():
        errors.append("File is empty")
    
    if "<rule>" not in content:
        errors.append("Missing <rule> opening tag")
    
    if "</rule>" not in content:
        errors.append("Missing </rule> closing tag")
    
    # Check for name attribute
    name_match = re.search(r'name:\s*(\w+)', content)
    if not name_match:
        errors.append("Missing rule name")
    else:
        rule_name = name_match.group(1)
        if not rule_name.islower() and not rule_name.startswith('_'):
            warnings.append("Rule name should be lowercase or start with underscore")
    
    # Check for description
    if 'description:' not in content:
        warnings.append("Missing rule description")
    
    # Check for filters
    if 'filters:' not in content:
        warnings.append("Missing filters section")
    
    # Check for actions
    if 'actions:' not in content:
        warnings.append("Missing actions section")
    
    # Check for proper indentation
    lines = content.split('\n')
    for i, line in enumerate(lines, 1):
        if line.strip() and not line.startswith(' ') and not line.startswith('\t'):
            if any(keyword in line for keyword in ['name:', 'description:', 'filters:', 'actions:']):
                if not line.startswith('  '):
                    warnings.append(f"Line {i}: Inconsistent indentation")
    
    # Check for examples
    if 'examples:' not in content:
        suggestions.append("Consider adding examples for better clarity")
    
    is_valid = len(errors) == 0
    
    return ValidationResult(
        is_valid=is_valid,
        errors=errors,
        warnings=warnings,
        suggestions=suggestions
    )


def validate_all_rules(project_root: str = ".") -> Dict[str, Any]:
    """
    Validates all Cursor rule files in the project.
    
    Args:
        project_root: Path to the project root directory
        
    Returns:
        Dictionary with comprehensive validation results
    """
    cursor_rules_dir = Path(project_root) / ".cursor" / "rules"
    
    if not cursor_rules_dir.exists():
        return {
            "valid": False,
            "error": f"Cursor rules directory not found: {cursor_rules_dir}",
            "files_validated": 0,
            "valid_files": 0,
            "invalid_files": 0
        }
    
    mdc_files = list(cursor_rules_dir.glob("*.mdc"))
    results = {
        "valid": True,
        "files_validated": len(mdc_files),
        "valid_files": 0,
        "invalid_files": 0,
        "file_details": {}
    }
    
    for mdc_file in mdc_files:
        validation = validate_rule_structure(str(mdc_file))
        file_name = mdc_file.name
        
        results["file_details"][file_name] = {
            "valid": validation.is_valid,
            "errors": validation.errors,
            "warnings": validation.warnings,
            "suggestions": validation.suggestions
        }
        
        if validation.is_valid:
            results["valid_files"] += 1
        else:
            results["invalid_files"] += 1
            results["valid"] = False
    
    return results


def generate_validation_report(project_root: str = ".") -> str:
    """
    Generates a comprehensive validation report for all Cursor rules.
    
    Args:
        project_root: Path to the project root directory
        
    Returns:
        Formatted validation report string
    """
    location_validation = validate_cursor_rules_location(project_root)
    all_rules_validation = validate_all_rules(project_root)
    
    report = []
    report.append("=" * 60)
    report.append("CURSOR RULES VALIDATION REPORT")
    report.append("=" * 60)
    report.append("")
    
    # Location validation
    report.append("📁 LOCATION VALIDATION")
    report.append("-" * 30)
    if location_validation["valid"]:
        report.append("✅ All rule files are in correct location")
    else:
        report.append("❌ Found rule files in wrong locations:")
        for error in location_validation["errors"]:
            report.append(f"   - {error}")
    
    if location_validation["warnings"]:
        report.append("\n⚠️  Warnings:")
        for warning in location_validation["warnings"]:
            report.append(f"   - {warning}")
    
    if location_validation["suggestions"]:
        report.append("\n💡 Suggestions:")
        for suggestion in location_validation["suggestions"]:
            report.append(f"   - {suggestion}")
    
    # Structure validation
    report.append("\n")
    report.append("🏗️  STRUCTURE VALIDATION")
    report.append("-" * 30)
    
    if "error" in all_rules_validation:
        report.append(f"❌ {all_rules_validation['error']}")
    else:
        report.append(f"📊 Files validated: {all_rules_validation['files_validated']}")
        report.append(f"✅ Valid files: {all_rules_validation['valid_files']}")
        report.append(f"❌ Invalid files: {all_rules_validation['invalid_files']}")
        
        if all_rules_validation["file_details"]:
            report.append("\n📋 File Details:")
            for file_name, details in all_rules_validation["file_details"].items():
                status = "✅" if details["valid"] else "❌"
                report.append(f"   {status} {file_name}")
                
                if details["errors"]:
                    for error in details["errors"]:
                        report.append(f"      - Error: {error}")
                
                if details["warnings"]:
                    for warning in details["warnings"]:
                        report.append(f"      - Warning: {warning}")
                
                if details["suggestions"]:
                    for suggestion in details["suggestions"]:
                        report.append(f"      - Suggestion: {suggestion}")
    
    report.append("\n" + "=" * 60)
    
    return "\n".join(report)


def main():
    """
    Main function to run validation and generate report.
    """
    print("🔍 Validating Cursor Rules...")
    print()
    
    report = generate_validation_report()
    print(report)
    
    # Check if validation passed
    location_validation = validate_cursor_rules_location()
    all_rules_validation = validate_all_rules()
    
    if location_validation["valid"] and all_rules_validation.get("valid", False):
        print("🎉 All validations passed!")
        return 0
    else:
        print("⚠️  Some validations failed. Check the report above.")
        return 1


if __name__ == "__main__":
    exit(main()) 
import os
import re
from pathlib import Path
from typing import List, Dict, Tuple, Optional

# Cursor rules validation and management utilities


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
    project_path = Path(project_root).resolve()
    cursor_rules_dir = project_path / ".cursor" / "rules"
    
    result = {
        "valid": True,
        "errors": [],
        "warnings": [],
        "valid_files": [],
        "invalid_files": [],
        "suggestions": []
    }
    
    # Find all .mdc files in the project
    mdc_files = list(project_path.rglob("*.mdc"))  # Recursively find all .mdc files
    
    if not mdc_files:
        result["warnings"].append("No .mdc files found in the project")
        return result
    
    for mdc_file in mdc_files:
        file_path = mdc_file.relative_to(project_path)
        
        # Check if file is in the correct location
        if str(file_path).startswith(".cursor/rules/"):  # Validate proper directory placement
            result["valid_files"].append(str(file_path))
            
            # Validate file content looks like a Cursor rule
            if _is_cursor_rule_file(mdc_file):
                result["suggestions"].append(f"✓ {file_path} is correctly placed and appears to be a valid Cursor rule")
            else:
                result["warnings"].append(f"⚠ {file_path} is in correct location but doesn't appear to contain Cursor rule content")
        else:
            result["invalid_files"].append(str(file_path))
            result["errors"].append(f"❌ {file_path} must be placed in .cursor/rules/ directory")
            result["valid"] = False
    
    # Check if .cursor/rules directory exists
    if not cursor_rules_dir.exists():
        result["warnings"].append("Directory .cursor/rules/ does not exist")
        result["suggestions"].append("Create directory structure: .cursor/rules/")
    
    # Add general suggestions
    if result["invalid_files"]:
        result["suggestions"].extend([
            "Move all .mdc files to .cursor/rules/ directory",
            "Follow naming convention: use kebab-case for filenames",
            "Ensure all rule files have .mdc extension"
        ])
    
    return result


def _is_cursor_rule_file(file_path: Path) -> bool:
    # Checks if file contains valid Cursor rule syntax
    """
    Checks if a file contains Cursor rule content.
    
    Args:
        file_path: Path to the file to check
        
    Returns:
        True if the file appears to contain Cursor rule content
    """
    try:
        content = file_path.read_text(encoding='utf-8')
        # Check for rule tags in the content
        rule_pattern = r'(?s)<rule>.*?</rule>'  # Match rule tags with multiline support
        return bool(re.search(rule_pattern, content))
    except (UnicodeDecodeError, IOError):
        return False


def create_cursor_rules_directory(project_root: str = ".") -> bool:
    # Creates .cursor/rules directory structure if missing
    """
    Creates the .cursor/rules directory structure if it doesn't exist.
    
    Args:
        project_root: Path to the project root directory
        
    Returns:
        True if directory was created or already exists, False otherwise
    """
    try:
        project_path = Path(project_root).resolve()
        cursor_rules_dir = project_path / ".cursor" / "rules"
        cursor_rules_dir.mkdir(parents=True, exist_ok=True)
        return True
    except Exception:
        return False


def move_cursor_rule_file(source_path: str, project_root: str = ".") -> Tuple[bool, str]:
    # Moves .mdc file to correct .cursor/rules location
    """
    Moves a Cursor rule file to the correct .cursor/rules directory.
    
    Args:
        source_path: Path to the source .mdc file
        project_root: Path to the project root directory
        
    Returns:
        Tuple of (success: bool, message: str)
    """
    try:
        source_file = Path(source_path)
        project_path = Path(project_root).resolve()
        target_dir = project_path / ".cursor" / "rules"
        
        if not source_file.exists():
            return False, f"Source file {source_path} does not exist"
        
        if not source_file.suffix == '.mdc':
            return False, f"File {source_path} is not a .mdc file"
        
        # Create target directory if it doesn't exist
        target_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate target filename using kebab-case
        filename = source_file.stem
        kebab_filename = re.sub(r'[^a-zA-Z0-9]+', '-', filename).strip('-').lower()  # Convert to kebab-case
        target_file = target_dir / f"{kebab_filename}.mdc"
        
        # Move the file
        source_file.rename(target_file)
        
        return True, f"Successfully moved {source_path} to {target_file.relative_to(project_path)}"
        
    except Exception as e:
        return False, f"Error moving file: {str(e)}"


def get_cursor_rules_summary(project_root: str = ".") -> str:
    # Returns formatted validation summary with results
    """
    Returns a formatted summary of Cursor rules validation.
    
    Args:
        project_root: Path to the project root directory
        
    Returns:
        Formatted string summary
    """
    validation = validate_cursor_rules_location(project_root)
    
    summary = "Cursor Rules Location Validation Summary\n"
    summary += "=" * 40 + "\n\n"
    
    if validation["valid"]:
        summary += "✅ All Cursor rule files are correctly placed!\n\n"
    else:
        summary += "❌ Found Cursor rule files in incorrect locations:\n"
        for error in validation["errors"]:
            summary += f"  {error}\n"
        summary += "\n"
    
    if validation["valid_files"]:
        summary += "✅ Correctly placed files:\n"
        for file in validation["valid_files"]:
            summary += f"  {file}\n"
        summary += "\n"
    
    if validation["warnings"]:
        summary += "⚠️  Warnings:\n"
        for warning in validation["warnings"]:
            summary += f"  {warning}\n"
        summary += "\n"
    
    if validation["suggestions"]:
        summary += "💡 Suggestions:\n"
        for suggestion in validation["suggestions"]:
            summary += f"  {suggestion}\n"
    
    return summary


# Example usage and testing
if __name__ == "__main__":
    # Example usage
    print(get_cursor_rules_summary())
    
    # Create directory structure
    if create_cursor_rules_directory():
        print("✅ Created .cursor/rules directory structure")
    else:
        print("❌ Failed to create directory structure") 
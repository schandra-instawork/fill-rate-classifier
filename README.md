# Cursor Rules Validator

A Python utility for validating and managing Cursor rule files (.mdc) to ensure they are placed in the correct directory structure according to Cursor's conventions.

## Overview

This tool helps enforce the Cursor rules location standard by:

- Validating that all `.mdc` files are placed in the `.cursor/rules/` directory
- Checking file content to ensure it contains valid Cursor rule syntax
- Providing utilities to move files to the correct location
- Converting filenames to kebab-case convention
- Generating comprehensive validation reports

## Features

- **Location Validation**: Ensures `.mdc` files are in the correct `.cursor/rules/` directory
- **Content Validation**: Checks if files contain valid Cursor rule syntax (`<rule>` tags)
- **File Movement**: Automatically moves files to the correct location
- **Kebab-case Conversion**: Converts filenames to proper naming convention
- **Directory Creation**: Creates the required directory structure
- **Comprehensive Reporting**: Provides detailed validation summaries

## Installation

No external dependencies required. The tool uses only Python standard library modules:

- `pathlib` - for file system operations
- `re` - for regular expressions
- `os` - for operating system interactions

## Usage

### Basic Validation

```python
from cursor_rules_validator import validate_cursor_rules_location

# Validate current project
result = validate_cursor_rules_location()

if result["valid"]:
    print("✅ All Cursor rule files are correctly placed!")
else:
    print("❌ Found issues with Cursor rule file placement")
    for error in result["errors"]:
        print(f"  {error}")
```

### Get Formatted Summary

```python
from cursor_rules_validator import get_cursor_rules_summary

# Get a formatted summary of validation results
summary = get_cursor_rules_summary()
print(summary)
```

### Create Directory Structure

```python
from cursor_rules_validator import create_cursor_rules_directory

# Create the .cursor/rules directory if it doesn't exist
success = create_cursor_rules_directory()
if success:
    print("✅ Directory structure created successfully")
```

### Move Files to Correct Location

```python
from cursor_rules_validator import move_cursor_rule_file

# Move a file to the correct location
success, message = move_cursor_rule_file("my-rule.mdc")
if success:
    print(f"✅ {message}")
else:
    print(f"❌ {message}")
```

## API Reference

### `validate_cursor_rules_location(project_root: str = ".") -> Dict[str, any]`

Validates that Cursor rule files are placed in the correct directory structure.

**Parameters:**
- `project_root` (str): Path to the project root directory (default: current directory)

**Returns:**
Dictionary with the following structure:
```python
{
    "valid": bool,           # Overall validation status
    "errors": List[str],     # List of error messages
    "warnings": List[str],   # List of warning messages
    "valid_files": List[str],    # List of correctly placed files
    "invalid_files": List[str],  # List of incorrectly placed files
    "suggestions": List[str]     # List of suggestions for improvement
}
```

### `create_cursor_rules_directory(project_root: str = ".") -> bool`

Creates the `.cursor/rules` directory structure if it doesn't exist.

**Parameters:**
- `project_root` (str): Path to the project root directory

**Returns:**
- `bool`: True if directory was created or already exists, False otherwise

### `move_cursor_rule_file(source_path: str, project_root: str = ".") -> Tuple[bool, str]`

Moves a Cursor rule file to the correct `.cursor/rules` directory.

**Parameters:**
- `source_path` (str): Path to the source `.mdc` file
- `project_root` (str): Path to the project root directory

**Returns:**
- `Tuple[bool, str]`: (success, message) - success status and descriptive message

### `get_cursor_rules_summary(project_root: str = ".") -> str`

Returns a formatted summary of Cursor rules validation.

**Parameters:**
- `project_root` (str): Path to the project root directory

**Returns:**
- `str`: Formatted summary string

## Directory Structure

The tool enforces the following directory structure:

```
PROJECT_ROOT/
├── .cursor/
│   └── rules/
│       ├── your-rule-name.mdc
│       ├── another-rule.mdc
│       └── ...
└── ...
```

## Naming Conventions

- Use kebab-case for filenames (e.g., `my-rule-name.mdc`)
- Always use `.mdc` extension
- Make names descriptive of the rule's purpose

## Examples

### Running the Example Script

```bash
python3 example_usage.py
```

This will demonstrate:
1. Checking current project state
2. Creating the required directory structure
3. Creating sample files in wrong locations
4. Validating and identifying issues
5. Moving files to correct locations
6. Showing the final organized structure

### Running Tests

```bash
python3 test_cursor_rules_validator.py
```

## Validation Rules

The tool validates according to these rules:

1. **Location Rule**: All `.mdc` files must be in `.cursor/rules/` directory
2. **Content Rule**: Files should contain `<rule>` tags to be considered valid Cursor rules
3. **Extension Rule**: Only files with `.mdc` extension are processed
4. **Naming Rule**: Filenames are converted to kebab-case when moved

## Error Handling

The tool handles various error scenarios:

- Non-existent files
- Permission errors
- Invalid file extensions
- Unicode encoding issues
- Directory creation failures

## Contributing

When contributing to this project:

1. Follow the existing code style
2. Add tests for new functionality
3. Update documentation as needed
4. Ensure all tests pass before submitting

## License

This project is open source and available under the MIT License.

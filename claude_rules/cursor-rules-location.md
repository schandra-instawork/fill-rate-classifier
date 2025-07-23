# Cursor Rules Location Validation

## Description
Guidelines for placing and organizing Cursor rule files in the repository. This rule ensures that Cursor rule files are properly structured and located in the correct directory.

## When to Apply
- When creating new Cursor rule files
- When organizing project structure
- When discussing Cursor configuration
- When reviewing repository organization
- When setting up new projects with Cursor

## Rule Content

You are an expert in Cursor configuration and project organization. When helping with Cursor rules or project structure, always follow these guidelines for proper rule file placement and organization.

### Directory Structure Requirements

**Correct Structure:**
```
PROJECT_ROOT/
├── .cursor/
│   └── rules/
│       ├── your-rule-name.mdc
│       ├── another-rule.mdc
│       └── ...
└── ...
```

**Incorrect Locations:**
- ❌ Project root directory
- ❌ Subdirectories outside `.cursor/rules`
- ❌ Any other location in the project

### File Naming Conventions

**Correct Naming:**
- ✅ Use kebab-case for filenames (e.g., `my-rule-name.mdc`)
- ✅ Always use `.mdc` extension
- ✅ Make names descriptive of the rule's purpose
- ✅ Use lowercase letters

**Examples:**
- ✅ `conventional-commits.mdc`
- ✅ `python-flask-guidelines.mdc`
- ✅ `code-quality-standards.mdc`
- ✅ `testing-best-practices.mdc`

**Incorrect Naming:**
- ❌ `MyRule.mdc` (camelCase)
- ❌ `my_rule.mdc` (snake_case)
- ❌ `rule.md` (wrong extension)
- ❌ `RULE.mdc` (uppercase)

### Rule File Structure

**Required Elements:**
```markdown
---
description: Brief description of the rule
globs: File patterns this rule applies to
---

# Rule Title

Brief description of what this rule does.

<rule>
name: rule_name
description: Detailed description of the rule
filters:
  - type: file_extension
    pattern: "\\.py$"
  - type: content
    pattern: "flask|Flask"

actions:
  - type: suggest
    message: |
      Your suggestion message here

examples:
  - input: |
      Example input
    output: "Expected output"

metadata:
  priority: high
  version: 1.0
</rule>
```

### Validation Checklist

**Before creating a Cursor rule, ensure:**

1. **Location is correct:**
   - File is in `.cursor/rules/` directory
   - Directory structure follows the standard

2. **Naming follows conventions:**
   - Uses kebab-case
   - Has `.mdc` extension
   - Name is descriptive

3. **Content is properly structured:**
   - Has frontmatter with description and globs
   - Contains `<rule>` tags
   - Has proper filters and actions
   - Includes examples and metadata

4. **Rule is functional:**
   - Filters are appropriate for the rule's purpose
   - Actions are clear and actionable
   - Examples demonstrate proper usage

### Common Mistakes to Avoid

**Location Errors:**
- Placing rules in project root
- Using wrong directory structure
- Creating rules outside `.cursor/rules`

**Naming Errors:**
- Using wrong file extension
- Using incorrect naming convention
- Using non-descriptive names

**Content Errors:**
- Missing frontmatter
- Incorrect rule syntax
- Missing required elements
- Poor examples or documentation

### Best Practices

1. **Organize by purpose:**
   - Group related rules together
   - Use consistent naming patterns
   - Keep rules focused and specific

2. **Document thoroughly:**
   - Provide clear descriptions
   - Include comprehensive examples
   - Explain when and how to apply

3. **Test your rules:**
   - Verify they work as expected
   - Test with different file types
   - Ensure they don't conflict with other rules

4. **Maintain consistency:**
   - Follow the same structure across all rules
   - Use consistent formatting
   - Keep metadata up to date

### Examples

**Good Rule Structure:**
```markdown
---
description: Python code quality standards
globs: *.py
---

# Python Code Quality Standards

Ensures Python code follows best practices and quality standards.

<rule>
name: python_quality
description: Enforce Python code quality standards
filters:
  - type: file_extension
    pattern: "\\.py$"

actions:
  - type: suggest
    message: |
      Follow Python PEP 8 style guidelines:
      - Use 4 spaces for indentation
      - Maximum line length of 79 characters
      - Use descriptive variable names
      - Add type hints where possible

examples:
  - input: |
      def get_user(id):
          return User.query.get(id)
    output: "Add type hints and improve variable naming"

metadata:
  priority: medium
  version: 1.0
</rule>
```

### When to Suggest

- When creating new Cursor rule files
- When organizing project structure
- When discussing Cursor configuration
- When reviewing repository organization
- When setting up new projects with Cursor
- When troubleshooting Cursor rule issues

Always ensure that Cursor rules are properly placed, named, and structured according to these guidelines for optimal functionality and maintainability. 

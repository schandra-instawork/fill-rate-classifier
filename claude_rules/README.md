# Claude Rules

This directory contains Claude rules that have been ported from the intelligent Cursor rules. These rules provide context-aware guidance and best practices for various development scenarios.

## Overview

Claude rules are designed to provide intelligent, context-aware assistance when working with code and development projects. Unlike Cursor rules which are automatically triggered, Claude rules are applied based on the conversation context and the specific scenarios being discussed.

## Available Rules

### 1. Conventional Commits (`conventional-commits.md`)
**Purpose**: Automatically suggest conventional commit formats when changes are made to code files.

**When to Apply**:
- When creating, modifying, or saving any file in the project
- When discussing git commits or version control
- When reviewing code changes that need to be committed

**Key Features**:
- Smart commit type detection based on changes
- Automatic scope extraction from file paths
- Comprehensive examples for all commit types
- Guidelines for proper commit message formatting

### 2. Python Flask Guidelines (`python-flask-guidelines.md`)
**Purpose**: Expert guidelines for Python, Flask, and scalable API development.

**When to Apply**:
- When working with Python files containing Flask code
- When creating new Flask applications or components
- When discussing API development, web services, or backend architecture
- When reviewing Flask code or providing code suggestions

**Key Features**:
- Application factory pattern guidance
- Blueprint organization best practices
- Error handling with guard clauses
- Database operations with SQLAlchemy
- Authentication with JWT
- Testing with pytest
- Performance optimization strategies
- Configuration management

### 3. Cursor Rules Location Validation (`cursor-rules-location.md`)
**Purpose**: Guidelines for placing and organizing Cursor rule files in the repository.

**When to Apply**:
- When creating new Cursor rule files
- When organizing project structure
- When discussing Cursor configuration
- When reviewing repository organization

**Key Features**:
- Directory structure requirements
- File naming conventions
- Rule file structure guidelines
- Validation checklist
- Common mistakes to avoid

## How to Use Claude Rules

### Method 1: Direct Application
When discussing a relevant topic, you can directly apply the rule by referencing its content and guidelines.

### Method 2: Context-Aware Suggestions
The rules are designed to be context-aware, so they will automatically provide relevant suggestions based on the conversation context.

### Method 3: Manual Reference
You can manually reference specific rules when you need guidance on particular topics.

## Rule Structure

Each Claude rule follows this structure:

1. **Description**: Brief overview of what the rule covers
2. **When to Apply**: Specific scenarios where the rule should be used
3. **Rule Content**: Detailed guidelines, examples, and best practices
4. **Context-Aware Suggestions**: Different advice for different situations
5. **Examples**: Practical examples showing proper implementation
6. **Best Practices**: Summary of key principles and guidelines

## Intelligence Features

### Context-Aware Filtering
- Rules provide different guidance based on the specific context
- Suggestions adapt to the current development scenario
- Examples are tailored to the specific use case

### Progressive Enhancement
- Basic guidance for general scenarios
- More specific advice as context becomes clearer
- Detailed examples for complex situations

### Best Practice Integration
- Rules incorporate industry best practices
- Guidelines are based on proven development patterns
- Suggestions promote maintainable and scalable code

## Benefits

### 🎯 **Precision**
- Rules provide targeted guidance for specific scenarios
- Suggestions are contextually relevant
- No generic or irrelevant advice

### 🚀 **Efficiency**
- Quick access to proven best practices
- Reduced time spent on research and decision-making
- Consistent application of standards

### 📚 **Learning**
- Educational content with explanations
- Progressive complexity in examples
- Best practices that can be applied broadly

### 🔧 **Consistency**
- Standardized approaches across projects
- Consistent code quality and structure
- Uniform commit message formatting

## Integration with Cursor Rules

These Claude rules complement the Cursor rules by providing:

1. **Conversational Context**: Detailed explanations and reasoning
2. **Educational Value**: Learning opportunities and best practice explanations
3. **Flexibility**: Can be applied in various conversation contexts
4. **Comprehensive Coverage**: Detailed guidelines beyond automated suggestions

## Future Enhancements

The Claude rules system can be extended with:

- Additional technology-specific rules (React, Node.js, etc.)
- Project management and workflow rules
- Code review and quality assurance rules
- Deployment and DevOps guidelines
- Security and performance best practices

## Usage Examples

### Example 1: Flask Development
**Context**: Discussing Flask application structure
**Applied Rule**: Python Flask Guidelines
**Result**: Detailed guidance on application factory pattern, blueprints, and best practices

### Example 2: Git Commits
**Context**: Making code changes that need to be committed
**Applied Rule**: Conventional Commits
**Result**: Automatic suggestion of proper commit format with type and scope

### Example 3: Project Organization
**Context**: Setting up Cursor rules in a new project
**Applied Rule**: Cursor Rules Location Validation
**Result**: Guidelines for proper rule placement and structure

## Contributing

To add new Claude rules:

1. Follow the established structure and format
2. Include comprehensive examples and guidelines
3. Ensure context-aware suggestions
4. Provide clear "When to Apply" criteria
5. Include best practices and common mistakes to avoid

The rules are designed to be intelligent, helpful, and contextually relevant for optimal development assistance. 
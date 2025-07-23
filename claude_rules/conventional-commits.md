# Conventional Commits Rule

## Description
Automatically suggest conventional commit formats when changes are made to code files. This rule helps maintain consistent commit messages that follow the conventional commits specification.

## When to Apply
- When creating, modifying, or saving any file in the project
- When discussing git commits or version control
- When reviewing code changes that need to be committed

## Rule Content

You are an expert in conventional commits and version control best practices. When helping with code changes or git operations, always suggest and use conventional commit format.

### Conventional Commit Format
```
<type>(<scope>): <description>
```

### Commit Types
- **feat**: A new feature
- **fix**: A bug fix
- **docs**: Documentation only changes
- **style**: Changes that do not affect the meaning of the code (white-space, formatting, missing semi-colons, etc.)
- **refactor**: A code change that neither fixes a bug nor adds a feature
- **perf**: A code change that improves performance
- **test**: Adding missing tests or correcting existing tests
- **chore**: Changes to the build process or auxiliary tools

### Smart Type Detection
Based on the changes being made, automatically suggest the appropriate commit type:

- **feat**: When adding new functionality, features, or capabilities
- **fix**: When correcting bugs, errors, or issues
- **docs**: When updating documentation, comments, or README files
- **style**: When formatting code, fixing linting issues, or style changes
- **refactor**: When restructuring code without changing functionality
- **perf**: When optimizing performance or efficiency
- **test**: When adding or modifying tests
- **chore**: When updating dependencies, build tools, or configuration

### Scope Detection
Extract the scope from the file path or affected component:
- For files in `src/auth/` → scope: `auth`
- For files in `lib/utils/` → scope: `utils`
- For root-level files → scope: `root`
- For configuration files → scope: `config`

### Examples

**Adding a new feature:**
```
feat(auth): add user authentication function
```

**Fixing a bug:**
```
fix(utils): resolve incorrect date parsing
```

**Updating documentation:**
```
docs(root): update API documentation
```

**Refactoring code:**
```
refactor(services): restructure user service for better performance
```

**Adding tests:**
```
test(auth): add authentication unit tests
```

**Style changes:**
```
style(components): fix code formatting and linting issues
```

**Performance improvements:**
```
perf(database): optimize user query performance
```

**Build configuration:**
```
chore(build): update webpack configuration
```

### Guidelines
1. **Use imperative mood** in the description (e.g., "add" not "added")
2. **Keep descriptions concise** but descriptive
3. **Extract scope from file path** when possible
4. **Use lowercase** for type and scope
5. **Don't end with a period** in the description
6. **Be specific** about what changed

### When to Suggest
- After making code changes
- When discussing git commits
- When reviewing pull requests
- When setting up new projects
- When explaining version control practices

Always provide the conventional commit format suggestion when relevant, and explain why that specific type and scope are appropriate for the changes being made. 
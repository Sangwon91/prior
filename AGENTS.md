# Development Guidelines for AI Agents

This document outlines the development guidelines and best practices for AI agents working on this codebase. Please follow these guidelines to ensure consistency and quality across all contributions.

## Package Management with uv

This project uses `uv` for package management. **Always use uv commands instead of traditional Python tools.**

### Adding Dependencies

- **Use `uv add`** instead of `pip install`
  ```bash
  # Correct
  uv add package-name
  
  # Incorrect
  pip install package-name
  ```

- **Use `uv run python`** instead of `python`
  ```bash
  # Correct
  uv run python script.py
  
  # Incorrect
  python script.py
  ```

### Workspace Structure

This is a uv workspace with multiple packages:
- `packages/agent` - Agent implementation
- `packages/tools` - Tool registry and utilities
- `packages/tui` - Terminal UI components
- `packages/workflow` - Workflow execution engine

Dependencies between workspace packages are managed automatically through the workspace configuration in `pyproject.toml`.

## Git Commit Conventions

**Always use conventional commit message prefixes** for clear and consistent commit history.

### Commit Message Format

Use these prefixes:
- `feat:` - New feature
- `fix:` - Bug fix
- `refactor:` - Code refactoring
- `chore:` - Maintenance tasks, dependency updates
- `docs:` - Documentation changes
- `test:` - Test additions or modifications
- `style:` - Code style changes (formatting, etc.)

### Examples

```bash
# Good
git commit -m "refactor: simplify graph node creation logic"
git commit -m "feat: add support for conditional workflow branches"
git commit -m "chore: update pytest to latest version"
git commit -m "fix: resolve memory leak in workflow executor"

# Bad
git commit -m "updated code"
git commit -m "changes"
git commit -m "fix bug"
```

**Keep commit messages clear and concise.** The prefix should accurately describe the type of change, followed by a brief description.

## Working with Sub-packages

When executing commands for a specific package, you have two options:

### Option 1: Navigate to Package Directory

```bash
cd packages/workflow
uv run pytest tests -v
```

### Option 2: Use `--from` Flag

```bash
uv run --from packages/workflow pytest packages/workflow/tests -v
```

Both approaches are valid. Choose based on context and convenience.

### Setting PYTHONPATH

For some commands, you may need to set `PYTHONPATH` to include the package source:

```bash
PYTHONPATH=packages/workflow/src uv run pytest packages/workflow/tests -v
```

## Code Formatting with ruff

**Always apply ruff formatting after making code changes.**

### Running ruff

```bash
# Format code
uv run ruff format .

# Check formatting
uv run ruff check .
```

### Column Limit

**The 80 column limit is strictly enforced.** This is the most important formatting rule.

```python
# Good - within 80 columns
def process_workflow(
    workflow_id: str,
    config: WorkflowConfig,
) -> WorkflowResult:
    pass

# Bad - exceeds 80 columns
def process_workflow(workflow_id: str, config: WorkflowConfig) -> WorkflowResult:
    pass
```

Other formatting rules can be applied flexibly, but the 80 column limit must always be respected.

## Testing Requirements

**Always run tests after making code changes.** This ensures that your changes don't break existing functionality.

### Running All Tests

```bash
# Using Makefile (recommended)
make test
# or
make test-all
```

### Running Package-Specific Tests

```bash
# Agent package
make test-agent
# or
PYTHONPATH=packages/agent/src uv run pytest packages/agent/tests -v

# TUI package
make test-tui

# Tools package
make test-tools

# Workflow package
make test-workflow

# Prior main package
make test-prior
```

### Test Execution Workflow

1. Make your code changes
2. Apply ruff formatting
3. Run relevant tests
4. Fix any failing tests
5. Re-run tests to confirm all pass

**Never commit code that has failing tests.**

## Test-Driven Development (TDD)

**This project follows TDD principles.** When implementing new features or fixing bugs:

### TDD Workflow

1. **Write tests first** - Start by writing a failing test that describes the desired behavior
   ```python
   def test_new_feature():
       result = new_functionality()
       assert result == expected_value
   ```

2. **Run tests** - Verify the test fails (red phase)
   ```bash
   uv run pytest tests/test_new_feature.py -v
   ```

3. **Implement minimal code** - Write just enough code to make the test pass (green phase)
   ```python
   def new_functionality():
       return expected_value
   ```

4. **Run tests again** - Confirm the test passes
   ```bash
   uv run pytest tests/test_new_feature.py -v
   ```

5. **Refactor** - Improve code quality while keeping tests green (refactor phase)
   - Apply ruff formatting
   - Improve code structure
   - Ensure all tests still pass

### TDD Benefits

- Ensures test coverage from the start
- Forces clear API design
- Provides safety net for refactoring
- Documents expected behavior through tests

### When to Write Tests

- **Always** when adding new functionality
- **Always** when fixing bugs (write a test that reproduces the bug first)
- **Always** when refactoring (ensure existing tests cover the behavior)

---

## Summary Checklist

Before committing any changes, ensure:

- [ ] Used `uv add` instead of `pip install` (if adding dependencies)
- [ ] Used `uv run python` instead of `python` (if running scripts)
- [ ] Applied ruff formatting with 80 column limit enforced
- [ ] All relevant tests pass
- [ ] Followed TDD workflow (tests written first)
- [ ] Commit message uses conventional prefix (`feat:`, `fix:`, `refactor:`, etc.)
- [ ] Commit message is clear and concise

Following these guidelines ensures consistent, high-quality contributions to the codebase.


# Development Scripts

This directory contains shell scripts for maintaining code quality in the RAG chatbot project.

## Available Scripts

### 🎨 format.sh
Automatically formats all Python code using Black and isort.

```bash
./scripts/format.sh
```

**What it does:**
- Sorts imports with isort (Black-compatible profile)
- Formats code with Black (88 character line length)
- Makes changes to files in-place

**When to use:** Before committing code or when you want to ensure consistent formatting.

---

### 🔍 check.sh
Validates code quality without making changes. Exits with error code if checks fail.

```bash
./scripts/check.sh
```

**What it does:**
1. Checks import sorting (isort --check-only)
2. Checks code formatting (black --check)
3. Runs Flake8 linting
4. Runs mypy type checking (warnings only)

**When to use:**
- Before pushing code
- In CI/CD pipelines
- To verify code quality without modifying files

---

### 📋 lint.sh
Runs linting and type checking tools, showing issues without failing.

```bash
./scripts/lint.sh
```

**What it does:**
- Runs Flake8 to find style violations
- Runs mypy for static type checking
- Non-blocking (always exits with success)

**When to use:** During development to identify potential issues.

---

### 🧪 test.sh
Runs the test suite with coverage reporting.

```bash
./scripts/test.sh
```

**What it does:**
- Executes all tests in backend/tests/
- Generates coverage reports (terminal + HTML)
- HTML report saved to htmlcov/index.html

**When to use:**
- After making code changes
- To verify test coverage
- Before pushing code

---

### 🚀 quality.sh
Runs the full quality check pipeline (format → lint → test).

```bash
./scripts/quality.sh
```

**What it does:**
1. Formats code (format.sh)
2. Runs linting (lint.sh)
3. Runs tests (test.sh)

**When to use:**
- Before committing significant changes
- When you want a comprehensive quality check
- As a pre-push hook

## Requirements

All scripts require the development dependencies to be installed:

```bash
uv sync --extra dev
```

## Configuration Files

The scripts use configuration from:
- `pyproject.toml` - Black, isort, mypy, pytest settings
- `.flake8` - Flake8 linting rules

## CI/CD Integration

For continuous integration, use:

```bash
# Install dependencies
uv sync --extra dev

# Run checks (fails on issues)
./scripts/check.sh

# Run tests
./scripts/test.sh
```

## Troubleshooting

**Scripts not executable?**
```bash
chmod +x scripts/*.sh
```

**Virtual environment issues?**
The scripts use `uv run` which automatically manages the virtual environment.

**Formatting conflicts?**
All tools are configured to work together. If you see conflicts:
1. Run `./scripts/format.sh` first
2. Then address any remaining linting issues

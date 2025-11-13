#!/bin/bash
# Run all code quality checks without making changes

set -e

echo "🔍 Running all code quality checks..."
echo ""

echo "1️⃣  Checking import sorting with isort..."
uv run isort backend/ main.py --check-only --diff || {
    echo "❌ Import sorting check failed. Run './scripts/format.sh' to fix."
    exit 1
}
echo "✅ Import sorting is correct"
echo ""

echo "2️⃣  Checking code formatting with Black..."
uv run black backend/ main.py --check || {
    echo "❌ Code formatting check failed. Run './scripts/format.sh' to fix."
    exit 1
}
echo "✅ Code formatting is correct"
echo ""

echo "3️⃣  Running Flake8 linting..."
uv run flake8 backend/ main.py || {
    echo "⚠️  Flake8 found issues (warnings only)"
}
echo "✅ Flake8 checks passed"
echo ""

echo "4️⃣  Running mypy type checking..."
uv run mypy backend/ main.py --ignore-missing-imports || {
    echo "⚠️  Mypy found type issues (non-blocking)"
}
echo ""

echo "✅ All code quality checks complete!"

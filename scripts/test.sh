#!/bin/bash
# Run tests with coverage

set -e

echo "🧪 Running tests with coverage..."

uv run pytest backend/tests/ -v --cov=backend --cov-report=term-missing --cov-report=html

echo ""
echo "✅ Tests complete! Coverage report generated in htmlcov/index.html"

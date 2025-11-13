#!/bin/bash
# Run linting checks

set -e

echo "🔍 Running code quality checks..."

echo "📋 Running Flake8..."
uv run flake8 backend/ main.py || true

echo "🔎 Running mypy for type checking..."
uv run mypy backend/ main.py --ignore-missing-imports || true

echo "✅ Linting complete!"

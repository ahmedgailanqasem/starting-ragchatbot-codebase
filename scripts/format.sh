#!/bin/bash
# Format code with Black and isort

set -e

echo "🎨 Running code formatters..."

echo "📦 Running isort to sort imports..."
uv run isort backend/ main.py

echo "⬛ Running Black to format code..."
uv run black backend/ main.py

echo "✅ Code formatting complete!"

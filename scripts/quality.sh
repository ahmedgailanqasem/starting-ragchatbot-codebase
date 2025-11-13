#!/bin/bash
# Run full quality check pipeline: format, lint, and test

set -e

echo "🚀 Running full quality check pipeline..."
echo ""

echo "Step 1: Formatting code..."
./scripts/format.sh
echo ""

echo "Step 2: Running linting checks..."
./scripts/lint.sh
echo ""

echo "Step 3: Running tests..."
./scripts/test.sh
echo ""

echo "✅ Quality check pipeline complete!"

#!/bin/bash
# Test runner script for World Cup Betting Insights CLI

set -e

echo "🧪 Running World Cup Betting Insights Tests"
echo "============================================"
echo ""

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo "❌ pytest not found. Installing test dependencies..."
    python3 -m pip install pytest pytest-cov pytest-asyncio httpx
fi

# Run tests
echo "📁 Test directory: tests/"
echo ""

# Run all tests with verbose output
pytest tests/ \
    --verbose \
    --tb=short \
    --cov=src \
    --cov-report=term-missing \
    --cov-report=html:htmlcov \
    "$@"

echo ""
echo "============================================"
echo "✅ Tests complete!"
echo ""
echo "📊 Coverage report generated at: htmlcov/index.html"
echo "   Open with: open htmlcov/index.html"

#!/bin/bash
# Test runner script with coverage reporting

set -e

echo "================================"
echo "Alfred AI Assistant Test Suite"
echo "================================"
echo ""

# Check if requirements are installed
if ! python -m pytest --version > /dev/null 2>&1; then
    echo "Installing test dependencies..."
    pip install -r requirements-dev.txt -q
fi

# Parse command line arguments
COVERAGE=${1:-false}
VERBOSE=${2:-false}

echo "Running tests..."
echo ""

if [ "$COVERAGE" = "--coverage" ]; then
    echo "Generating coverage report..."
    if [ "$VERBOSE" = "-v" ]; then
        pytest tests/unit/ -v --cov=src --cov-report=html --cov-report=term-missing
    else
        pytest tests/unit/ --cov=src --cov-report=html --cov-report=term-missing
    fi
    echo ""
    echo "Coverage HTML report: htmlcov/index.html"
else
    if [ "$VERBOSE" = "-v" ]; then
        pytest tests/unit/ -v --tb=short
    else
        pytest tests/unit/ --tb=line
    fi
fi

echo ""
echo "================================"
echo "Test run complete!"
echo "================================"

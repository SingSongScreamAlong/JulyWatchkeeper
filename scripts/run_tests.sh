#!/bin/bash

# Script to run WATCHKEEPER tests with virtual environment
set -e

ECHO_PREFIX="[WATCHKEEPER Tests]"
VENV_DIR=".venv"
PROJECT_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")" && cd .. && pwd)

echo "$ECHO_PREFIX Running WATCHKEEPER tests"

# Check if virtual environment exists
if [ ! -d "$PROJECT_ROOT/$VENV_DIR" ]; then
    echo "$ECHO_PREFIX Virtual environment not found. Setting up..."
    "$PROJECT_ROOT/scripts/setup_venv.sh"
fi

# Activate virtual environment
echo "$ECHO_PREFIX Activating virtual environment..."
source "$PROJECT_ROOT/$VENV_DIR/bin/activate"

# Run the tests
echo "$ECHO_PREFIX Running tests..."
cd "$PROJECT_ROOT"

# Check if specific test file was provided
if [ -z "$1" ]; then
    # Run all tests
    python -m pytest tests/
else
    # Run specific test file
    python -m pytest "$1"
fi

#!/bin/bash

# Script to set up a Python virtual environment for WATCHKEEPER
set -e

ECHO_PREFIX="[WATCHKEEPER Setup]"
VENV_DIR=".venv"
PROJECT_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")" && cd .. && pwd)

echo "$ECHO_PREFIX Setting up Python virtual environment in $PROJECT_ROOT/$VENV_DIR"

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "$ECHO_PREFIX Python 3 is not installed. Please install Python 3 and try again."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "$PROJECT_ROOT/$VENV_DIR" ]; then
    echo "$ECHO_PREFIX Creating virtual environment..."
    python3 -m venv "$PROJECT_ROOT/$VENV_DIR"
else
    echo "$ECHO_PREFIX Virtual environment already exists."
fi

# Activate virtual environment
echo "$ECHO_PREFIX Activating virtual environment..."
source "$PROJECT_ROOT/$VENV_DIR/bin/activate"

# Install dependencies
echo "$ECHO_PREFIX Installing dependencies..."
pip install --upgrade pip
pip install -r "$PROJECT_ROOT/requirements.txt"

echo "$ECHO_PREFIX Setup complete! Virtual environment is activated."
echo "$ECHO_PREFIX To activate the virtual environment in the future, run:"
echo "source $PROJECT_ROOT/$VENV_DIR/bin/activate"

# Print instructions for running tests and server
echo ""
echo "$ECHO_PREFIX To run tests:"
echo "cd $PROJECT_ROOT && python -m pytest tests/"
echo ""
echo "$ECHO_PREFIX To run the API server:"
echo "cd $PROJECT_ROOT && python run.py"

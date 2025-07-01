#!/bin/bash

# Script to run the WATCHKEEPER API server with virtual environment
set -e

ECHO_PREFIX="[WATCHKEEPER API]"
VENV_DIR=".venv"
PROJECT_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")" && cd .. && pwd)

echo "$ECHO_PREFIX Starting WATCHKEEPER API server"

# Check if virtual environment exists
if [ ! -d "$PROJECT_ROOT/$VENV_DIR" ]; then
    echo "$ECHO_PREFIX Virtual environment not found. Setting up..."
    "$PROJECT_ROOT/scripts/setup_venv.sh"
fi

# Activate virtual environment
echo "$ECHO_PREFIX Activating virtual environment..."
source "$PROJECT_ROOT/$VENV_DIR/bin/activate"

# Run the API server
echo "$ECHO_PREFIX Running API server..."
cd "$PROJECT_ROOT"
python run.py

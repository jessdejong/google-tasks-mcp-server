#!/bin/bash
# Wrapper script to start the Google Tasks MCP server with the correct environment

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Change to the script directory
cd "$SCRIPT_DIR"

# Check if virtual environment exists
if [ -d ".venv" ]; then
    # Use the virtual environment
    exec "$SCRIPT_DIR/.venv/bin/python" "$SCRIPT_DIR/run_server.py"
else
    # Fall back to system python
    exec python3 "$SCRIPT_DIR/run_server.py"
fi

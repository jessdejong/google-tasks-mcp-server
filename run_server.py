#!/usr/bin/env python3
"""
Wrapper script to ensure the MCP server runs with the correct environment.
This script should be used in the Gemini CLI configuration instead of main.py.
"""

import os
import sys
from pathlib import Path

# Ensure we're in the correct directory
script_dir = Path(__file__).parent
os.chdir(script_dir)

# Add the current directory to Python path
sys.path.insert(0, str(script_dir))

# Set environment variables to help with debugging
os.environ['GOOGLE_TASKS_DEBUG'] = '1'

# Import and run the server
if __name__ == "__main__":
    try:
        from server import main
        main()
    except Exception as e:
        print(f"Error starting server: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)

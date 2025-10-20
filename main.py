#!/usr/bin/env python3
"""
Main entry point for the Google Tasks MCP Server.
"""

from server import main as server_main


def main():
    """Main entry point."""
    print("Starting Google Tasks MCP Server...")
    server_main()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Debug script to test authentication in different environments.
"""

import os
import sys
import json
from pathlib import Path

# Add the current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

def debug_environment():
    """Debug the current environment."""
    print("🔍 Environment Debug Information")
    print("=" * 50)
    print(f"Python executable: {sys.executable}")
    print(f"Current working directory: {os.getcwd()}")
    print(f"Script directory: {current_dir}")
    print(f"Python path: {sys.path[:3]}...")
    
    # Check for credential files
    creds_file = current_dir / "credentials.json"
    token_file = current_dir / "token.json"
    
    print(f"\n📁 File Check:")
    print(f"credentials.json exists: {creds_file.exists()}")
    print(f"token.json exists: {token_file.exists()}")
    
    if token_file.exists():
        try:
            with open(token_file, 'r') as f:
                token_data = json.load(f)
                print(f"Token keys: {list(token_data.keys())}")
                if 'expiry' in token_data:
                    print(f"Token expires: {token_data['expiry']}")
        except Exception as e:
            print(f"Error reading token: {e}")
    
    # Test imports
    print(f"\n📦 Import Test:")
    try:
        from server import get_google_tasks_service
        print("✅ Successfully imported get_google_tasks_service")
        
        # Test authentication
        print(f"\n🔐 Authentication Test:")
        service = get_google_tasks_service()
        if service:
            print("✅ Google Tasks service created successfully")
            try:
                tasklists = service.tasklists().list().execute()
                print(f"✅ API call successful, found {len(tasklists.get('items', []))} task lists")
            except Exception as e:
                print(f"❌ API call failed: {e}")
        else:
            print("❌ Failed to create Google Tasks service")
            
    except Exception as e:
        print(f"❌ Import failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_environment()

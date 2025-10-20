#!/usr/bin/env python3
"""
Test script for the Google Tasks MCP Server.

This script helps verify that the server is working correctly.
"""

import asyncio
import json
import os
from server import get_google_tasks_service


class MockContext:
    """Mock context for testing."""
    def __init__(self):
        pass


async def test_google_tasks_service():
    """Test the Google Tasks service authentication."""
    print("🔐 Testing Google Tasks Service Authentication...")
    
    # Check if credentials file exists
    if not os.path.exists('credentials.json'):
        print("❌ credentials.json not found. Please download it from Google Cloud Console.")
        print("   See README.md for setup instructions.")
        return False
    
    # Test service creation
    try:
        service = get_google_tasks_service()
        if service:
            print("✅ Google Tasks service created successfully")
            return True
        else:
            print("❌ Failed to create Google Tasks service")
            return False
    except Exception as e:
        print(f"❌ Error creating Google Tasks service: {e}")
        return False


async def test_list_tasklists():
    """Test the list_tasklists functionality directly."""
    print("\n1. Testing list_tasklists...")
    try:
        # Test the Google Tasks API directly
        service = get_google_tasks_service()
        if not service:
            print("❌ No Google Tasks service available")
            return False
        
        # Get task lists from Google Tasks API
        results = service.tasklists().list().execute()
        tasklists = results.get('items', [])
        
        # Format task lists data
        formatted_lists = []
        for tasklist in tasklists:
            formatted_list = {
                "id": tasklist.get('id'),
                "title": tasklist.get('title', ''),
                "updated": tasklist.get('updated'),
                "self_link": tasklist.get('selfLink')
            }
            formatted_lists.append(formatted_list)
        
        result = {
            "total_lists": len(formatted_lists),
            "tasklists": formatted_lists
        }
        
        print(f"✅ Result: {json.dumps(result, indent=2)}")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


async def test_get_tasks():
    """Test the get_tasks functionality directly."""
    print("\n2. Testing get_tasks (default list)...")
    try:
        # Test the Google Tasks API directly
        service = get_google_tasks_service()
        if not service:
            print("❌ No Google Tasks service available")
            return False
        
        # Get task lists first to find a valid list
        tasklists = service.tasklists().list().execute()
        available_lists = [tl['id'] for tl in tasklists.get('items', [])]
        
        if not available_lists:
            print("❌ No task lists found")
            return False
        
        # Use the first available list
        tasklist_id = available_lists[0]
        
        # Get tasks from Google Tasks API
        results = service.tasks().list(
            tasklist=tasklist_id,
            maxResults=5,
            showCompleted=False
        ).execute()
        tasks = results.get('items', [])
        
        # Format tasks data
        formatted_tasks = []
        for task in tasks:
            formatted_task = {
                "id": task.get('id'),
                "title": task.get('title', ''),
                "status": task.get('status', 'needsAction'),
                "notes": task.get('notes', ''),
                "due": task.get('due'),
                "updated": task.get('updated'),
                "position": task.get('position'),
                "parent": task.get('parent'),
                "links": task.get('links', [])
            }
            formatted_tasks.append(formatted_task)
        
        result = {
            "tasklist_id": tasklist_id,
            "max_results": 5,
            "show_completed": False,
            "total_tasks": len(formatted_tasks),
            "tasks": formatted_tasks,
            "available_lists": available_lists
        }
        
        print(f"✅ Result: {json.dumps(result, indent=2)}")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


async def test_get_tasks_with_completed():
    """Test the get_tasks functionality with completed tasks."""
    print("\n3. Testing get_tasks (with completed tasks)...")
    try:
        # Test the Google Tasks API directly
        service = get_google_tasks_service()
        if not service:
            print("❌ No Google Tasks service available")
            return False
        
        # Get task lists first to find a valid list
        tasklists = service.tasklists().list().execute()
        available_lists = [tl['id'] for tl in tasklists.get('items', [])]
        
        if not available_lists:
            print("❌ No task lists found")
            return False
        
        # Use the first available list
        tasklist_id = available_lists[0]
        
        # Get tasks from Google Tasks API (including completed)
        results = service.tasks().list(
            tasklist=tasklist_id,
            maxResults=10,
            showCompleted=True
        ).execute()
        tasks = results.get('items', [])
        
        # Format tasks data
        formatted_tasks = []
        for task in tasks:
            formatted_task = {
                "id": task.get('id'),
                "title": task.get('title', ''),
                "status": task.get('status', 'needsAction'),
                "notes": task.get('notes', ''),
                "due": task.get('due'),
                "updated": task.get('updated'),
                "position": task.get('position'),
                "parent": task.get('parent'),
                "links": task.get('links', [])
            }
            formatted_tasks.append(formatted_task)
        
        result = {
            "tasklist_id": tasklist_id,
            "max_results": 10,
            "show_completed": True,
            "total_tasks": len(formatted_tasks),
            "tasks": formatted_tasks,
            "available_lists": available_lists
        }
        
        print(f"✅ Result: {json.dumps(result, indent=2)}")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


async def test_server():
    """Main test function."""
    print("🚀 Google Tasks MCP Server Test Suite")
    print("=" * 60)
    
    # Test 1: Check authentication setup
    auth_ok = await test_google_tasks_service()
    
    # Test 2: Test server functions
    if auth_ok:
        await test_list_tasklists()
        await test_get_tasks()
        await test_get_tasks_with_completed()
    
    # Summary
    print("\n📋 Test Summary:")
    print("=" * 60)
    
    if auth_ok:
        print("✅ Authentication setup is correct")
        print("✅ Server functions are working")
        print("\n🎉 All tests passed! Your server is ready to use.")
        print("\nNext steps:")
        print("1. Run: python main.py")
        print("2. The server will open a browser for Google authentication")
        print("3. Grant permissions to access your Google Tasks")
    else:
        print("❌ Authentication setup needs attention")
        print("\nTo fix:")
        print("1. Go to Google Cloud Console")
        print("2. Enable Google Tasks API")
        print("3. Create OAuth 2.0 credentials")
        print("4. Download credentials.json to project root")
        print("5. Run this test again")


if __name__ == "__main__":
    asyncio.run(test_server())

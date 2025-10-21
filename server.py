#!/usr/bin/env python3
"""
Google Tasks MCP Server

A Model Context Protocol server that provides access to Google Tasks API.
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional

from fastmcp import FastMCP, Context
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Google Tasks API configuration
# Use full write scope since we implement create/update/delete operations
SCOPES = ['https://www.googleapis.com/auth/tasks']

# Get the directory where this script is located
import os
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CREDENTIALS_FILE = os.path.join(SCRIPT_DIR, 'credentials.json')
TOKEN_FILE = os.path.join(SCRIPT_DIR, 'token.json')

# Initialize the FastMCP server
mcp = FastMCP("google-tasks-mcp-server")


def get_google_tasks_service():
    """Get authenticated Google Tasks service."""
    creds = None
    
    logger.info(f"Looking for credentials at: {CREDENTIALS_FILE}")
    logger.info(f"Looking for token at: {TOKEN_FILE}")
    logger.info(f"Current working directory: {os.getcwd()}")
    
    # Try loading token from environment variable first (for deployment)
    token_env = os.getenv('GOOGLE_TASKS_TOKEN')
    if token_env:
        try:
            logger.info("Loading token from GOOGLE_TASKS_TOKEN environment variable...")
            import json
            token_info = json.loads(token_env)
            creds = Credentials.from_authorized_user_info(token_info, SCOPES)
        except Exception as e:
            logger.error(f"Failed to load token from environment: {e}")
            creds = None
    
    # Fallback to loading from file
    if not creds and os.path.exists(TOKEN_FILE):
        logger.info("Token file found, loading credentials...")
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    elif not creds:
        logger.warning(f"Token not found in environment or at: {TOKEN_FILE}")
    
    # If there are no (valid) credentials available, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                logger.error(f"Failed to refresh credentials: {e}")
                return None
        else:
            if not os.path.exists(CREDENTIALS_FILE):
                logger.error(f"Credentials file '{CREDENTIALS_FILE}' not found. Please download it from Google Cloud Console.")
                return None
            
            try:
                flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
                # Check if we're running in an interactive environment
                if os.isatty(0) and os.isatty(1):  # stdin and stdout are terminals
                    # Interactive mode - use local server
                    creds = flow.run_local_server(port=0)
                else:
                    # Non-interactive mode (like MCP) - use local server with port 0
                    # This will still work but may require manual URL copying
                    creds = flow.run_local_server(port=0)
            except Exception as e:
                logger.error(f"Authentication failed: {e}")
                logger.error("Please run the server interactively first to complete authentication:")
                logger.error("python3 main.py")
                return None
        
        # Save the credentials for the next run
        try:
            with open(TOKEN_FILE, 'w') as token:
                token.write(creds.to_json())
        except Exception as e:
            logger.error(f"Failed to save token: {e}")
    
    try:
        service = build('tasks', 'v1', credentials=creds)
        return service
    except Exception as e:
        logger.error(f"Error building Google Tasks service: {e}")
        return None


@mcp.tool
async def get_tasks(
    ctx: Context,
    tasklist_id: str = "@default",
    max_results: int = 100,
    show_completed: bool = False,
    show_deleted: bool = False
) -> dict:
    """
    Get tasks from Google Tasks API.
    
    Args:
        ctx: FastMCP context
        tasklist_id: ID of the task list (default: "@default")
        max_results: Maximum number of tasks to return (default: 100)
        show_completed: Whether to include completed tasks (default: false)
        show_deleted: Whether to include deleted tasks (default: false)
    
    Returns:
        Dictionary containing the tasks data
    """
    try:
        logger.info(f"Getting tasks from list: {tasklist_id}")
        
        # Get authenticated Google Tasks service
        service = get_google_tasks_service()
        if not service:
            return {
                "error": "Failed to authenticate with Google Tasks API. Please check your credentials.",
                "tasklist_id": tasklist_id,
                "tasks": []
            }
        
        # Get task lists first to validate tasklist_id
        tasklists = service.tasklists().list().execute()
        available_lists = [tl['id'] for tl in tasklists.get('items', [])]
        
        # If tasklist_id is "@default", use the first available list
        if tasklist_id == "@default":
            if not available_lists:
                return {
                    "error": "No task lists found in your Google Tasks account.",
                    "tasklist_id": tasklist_id,
                    "tasks": []
                }
            tasklist_id = available_lists[0]
        elif tasklist_id not in available_lists:
            return {
                "error": f"Task list '{tasklist_id}' not found. Available lists: {available_lists}",
                "tasklist_id": tasklist_id,
                "available_lists": available_lists,
                "tasks": []
            }
        
        # Build query parameters
        query_params = {
            'tasklist': tasklist_id,
            'maxResults': max_results
        }
        
        # Add completion filter
        if not show_completed:
            query_params['showCompleted'] = False
        else:
            query_params['showCompleted'] = True
            
        # Add deleted filter
        if not show_deleted:
            query_params['showDeleted'] = False
        else:
            query_params['showDeleted'] = True
        
        # Get tasks from Google Tasks API
        results = service.tasks().list(**query_params).execute()
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
        
        return {
            "tasklist_id": tasklist_id,
            "max_results": max_results,
            "show_completed": show_completed,
            "show_deleted": show_deleted,
            "total_tasks": len(formatted_tasks),
            "tasks": formatted_tasks,
            "available_lists": available_lists
        }
        
    except HttpError as e:
        logger.error(f"Google Tasks API error: {e}")
        return {
            "error": f"Google Tasks API error: {str(e)}",
            "tasklist_id": tasklist_id,
            "tasks": []
        }
    except Exception as e:
        logger.error(f"Error getting tasks: {e}")
        return {
            "error": f"Error retrieving tasks: {str(e)}",
            "tasklist_id": tasklist_id,
            "tasks": []
        }


@mcp.tool
async def list_tasklists(ctx: Context) -> dict:
    """
    List all available task lists from Google Tasks.
    
    Use this to discover available task lists before creating or querying tasks.
    Each user typically has at least one default task list, but may have multiple
    lists to organize different types of tasks.
    
    Args:
        ctx: FastMCP context
    
    Returns:
        Dictionary with 'total_lists' (count) and 'tasklists' (array of list objects).
        Each tasklist contains: id, title, updated timestamp, and self_link.
    """
    try:
        logger.info("Getting available task lists")
        
        # Get authenticated Google Tasks service
        service = get_google_tasks_service()
        if not service:
            return {
                "error": "Failed to authenticate with Google Tasks API. Please check your credentials.",
                "tasklists": []
            }
        
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
        
        return {
            "total_lists": len(formatted_lists),
            "tasklists": formatted_lists
        }
        
    except HttpError as e:
        logger.error(f"Google Tasks API error: {e}")
        return {
            "error": f"Google Tasks API error: {str(e)}",
            "tasklists": []
        }
    except Exception as e:
        logger.error(f"Error getting task lists: {e}")
        return {
            "error": f"Error retrieving task lists: {str(e)}",
            "tasklists": []
        }


def _resolve_tasklist_id(service, tasklist_id: str) -> dict:
    """Resolve '@default' to a real tasklist id and return metadata.

    Returns a dict: { 'tasklist_id': str, 'available_lists': [ids...] }
    """
    tasklists = service.tasklists().list().execute()
    available_lists = [tl['id'] for tl in tasklists.get('items', [])]
    if tasklist_id == "@default":
        if not available_lists:
            return {"error": "No task lists found.", "available_lists": []}
        return {"tasklist_id": available_lists[0], "available_lists": available_lists}
    if tasklist_id not in available_lists:
        return {
            "error": f"Task list '{tasklist_id}' not found.",
            "available_lists": available_lists,
        }
    return {"tasklist_id": tasklist_id, "available_lists": available_lists}


@mcp.tool
async def create_task(
    ctx: Context,
    title: str,
    due: str,
    tasklist_id: str = "@default",
    notes: Optional[str] = None,
    parent: Optional[str] = None,
    position: Optional[str] = None,
) -> dict:
    """
    Create a new task in Google Tasks with a due date.
    
    All tasks must have a due date. Google Tasks API only supports due dates, not 
    specific times. If you need to track a specific time for a task, add it to the 
    task title or notes field instead (e.g., "Meeting at 3 PM" or add "Time: 3 PM" 
    in the notes).

    Args:
        ctx: FastMCP context
        title: The title/name of the task (required)
        due: Due date in YYYY-MM-DD format (e.g., "2024-12-31") (required)
        tasklist_id: ID of the task list to add to (default: "@default" uses first list)
        notes: Optional description or notes for the task
        parent: Optional parent task ID to create a subtask
        position: Optional ID of the task to insert after (for ordering)

    Returns:
        Dictionary with 'tasklist_id' and 'task' (the created task object)
    """
    from datetime import datetime
    
    try:
        service = get_google_tasks_service()
        if not service:
            return {"error": "Auth failed"}
        resolved = _resolve_tasklist_id(service, tasklist_id)
        if "error" in resolved:
            return {"error": resolved["error"], **resolved}
        tasklist_id = resolved["tasklist_id"]

        # Format due date to RFC 3339 format
        try:
            # If it's already in RFC 3339 format (has 'T'), use as is
            if 'T' in due:
                due_formatted = due
            else:
                # Parse YYYY-MM-DD and convert to RFC 3339 format
                date_obj = datetime.strptime(due, "%Y-%m-%d")
                due_formatted = date_obj.strftime("%Y-%m-%dT00:00:00.000Z")
        except ValueError as e:
            return {"error": f"Invalid date format. Please use YYYY-MM-DD format (e.g., '2024-12-31'). Error: {str(e)}"}

        body: Dict[str, Any] = {"title": title, "due": due_formatted}
        if notes is not None:
            body["notes"] = notes

        insert_kwargs: Dict[str, Any] = {"tasklist": tasklist_id, "body": body}
        if parent is not None:
            insert_kwargs["parent"] = parent
        if position is not None:
            insert_kwargs["previous"] = position

        created = service.tasks().insert(**insert_kwargs).execute()
        return {"tasklist_id": tasklist_id, "task": created}
    except HttpError as e:
        logger.error(f"Google Tasks API error: {e}")
        return {"error": f"Google Tasks API error: {str(e)}"}
    except Exception as e:
        logger.error(f"Error creating task: {e}")
        return {"error": str(e)}


@mcp.tool
async def update_task(
    ctx: Context,
    task_id: str,
    tasklist_id: str = "@default",
    title: Optional[str] = None,
    notes: Optional[str] = None,
    due: Optional[str] = None,
    status: Optional[str] = None,
    parent: Optional[str] = None,
    position: Optional[str] = None,
) -> dict:
    """
    Update one or more fields of an existing task in Google Tasks.
    
    Only the fields you provide will be updated; all other fields remain unchanged.
    This allows for partial updates without needing to fetch and resend all task data.
    
    Args:
        ctx: FastMCP context
        task_id: The ID of the task to update (required)
        tasklist_id: ID of the task list containing the task (default: "@default")
        title: New title for the task
        notes: New description/notes for the task
        due: New due date in RFC 3339 format (e.g., "2024-12-31T23:59:59Z")
        status: New status - either "needsAction" or "completed"
        parent: New parent task ID to move this task under (makes it a subtask)
        position: ID of task to position this task after (for reordering)
    
    Returns:
        Dictionary with 'tasklist_id' and 'task' (the updated task object)
    """
    try:
        service = get_google_tasks_service()
        if not service:
            return {"error": "Auth failed"}
        resolved = _resolve_tasklist_id(service, tasklist_id)
        if "error" in resolved:
            return {"error": resolved["error"], **resolved}
        tasklist_id = resolved["tasklist_id"]

        # Fetch current task
        current = service.tasks().get(tasklist=tasklist_id, task=task_id).execute()
        body: Dict[str, Any] = {}
        if title is not None:
            body["title"] = title
        if notes is not None:
            body["notes"] = notes
        if due is not None:
            body["due"] = due
        if status is not None:
            body["status"] = status

        # PATCH to avoid overwriting unspecified fields
        updated = service.tasks().patch(tasklist=tasklist_id, task=task_id, body=body).execute()

        # Reparent/reposition if requested
        if parent is not None or position is not None:
            move_kwargs: Dict[str, Any] = {"tasklist": tasklist_id, "task": task_id}
            if parent is not None:
                move_kwargs["parent"] = parent
            if position is not None:
                move_kwargs["previous"] = position
            updated = service.tasks().move(**move_kwargs).execute()

        return {"tasklist_id": tasklist_id, "task": updated}
    except HttpError as e:
        logger.error(f"Google Tasks API error: {e}")
        return {"error": f"Google Tasks API error: {str(e)}"}
    except Exception as e:
        logger.error(f"Error updating task: {e}")
        return {"error": str(e)}


@mcp.tool
async def complete_task(
    ctx: Context,
    task_id: str,
    tasklist_id: str = "@default",
    completed: bool = True,
) -> dict:
    """
    Mark a task as completed or uncompleted (reopen it).
    
    This is a convenience function that updates the task's status field.
    When marking a task as completed, Google Tasks automatically sets the
    completion timestamp.
    
    Args:
        ctx: FastMCP context
        task_id: The ID of the task to update (required)
        tasklist_id: ID of the task list containing the task (default: "@default")
        completed: True to mark completed, False to mark as needs action (default: True)
    
    Returns:
        Dictionary with 'tasklist_id' and 'task' (the updated task object)
    """
    try:
        service = get_google_tasks_service()
        if not service:
            return {"error": "Auth failed"}
        resolved = _resolve_tasklist_id(service, tasklist_id)
        if "error" in resolved:
            return {"error": resolved["error"], **resolved}
        tasklist_id = resolved["tasklist_id"]

        status = "completed" if completed else "needsAction"
        updated = service.tasks().patch(
            tasklist=tasklist_id, task=task_id, body={"status": status}
        ).execute()
        return {"tasklist_id": tasklist_id, "task": updated}
    except HttpError as e:
        logger.error(f"Google Tasks API error: {e}")
        return {"error": f"Google Tasks API error: {str(e)}"}
    except Exception as e:
        logger.error(f"Error completing task: {e}")
        return {"error": str(e)}


@mcp.tool
async def delete_task(
    ctx: Context,
    task_id: str,
    tasklist_id: str = "@default",
) -> dict:
    """
    Permanently delete a task from Google Tasks.
    
    Warning: This action cannot be undone. The task will be permanently removed
    from the task list. If you want to preserve the task but mark it as done,
    use complete_task instead.
    
    Args:
        ctx: FastMCP context
        task_id: The ID of the task to delete (required)
        tasklist_id: ID of the task list containing the task (default: "@default")
    
    Returns:
        Dictionary with 'tasklist_id', 'deleted' (True), and 'task_id'
    """
    try:
        service = get_google_tasks_service()
        if not service:
            return {"error": "Auth failed"}
        resolved = _resolve_tasklist_id(service, tasklist_id)
        if "error" in resolved:
            return {"error": resolved["error"], **resolved}
        tasklist_id = resolved["tasklist_id"]

        service.tasks().delete(tasklist=tasklist_id, task=task_id).execute()
        return {"tasklist_id": tasklist_id, "deleted": True, "task_id": task_id}
    except HttpError as e:
        logger.error(f"Google Tasks API error: {e}")
        return {"error": f"Google Tasks API error: {str(e)}"}
    except Exception as e:
        logger.error(f"Error deleting task: {e}")
        return {"error": str(e)}


@mcp.tool
async def create_tasklist(ctx: Context, title: str) -> dict:
    """
    Create a new task list in Google Tasks.
    
    Task lists are top-level containers for organizing tasks. Users can have
    multiple task lists to separate different projects, contexts, or categories
    of tasks (e.g., "Work", "Personal", "Shopping").
    
    Args:
        ctx: FastMCP context
        title: The name/title for the new task list (required)
    
    Returns:
        Dictionary with 'tasklist' (the created tasklist object including its id)
    """
    try:
        service = get_google_tasks_service()
        if not service:
            return {"error": "Auth failed"}
        created = service.tasklists().insert(body={"title": title}).execute()
        return {"tasklist": created}
    except HttpError as e:
        logger.error(f"Google Tasks API error: {e}")
        return {"error": f"Google Tasks API error: {str(e)}"}
    except Exception as e:
        logger.error(f"Error creating task list: {e}")
        return {"error": str(e)}


@mcp.tool
async def get_task(
    ctx: Context,
    task_id: str,
    tasklist_id: str = "@default",
) -> dict:
    """
    Fetch detailed information about a single task by its ID.
    
    Use this when you need to retrieve or refresh the current state of a specific
    task, including all its properties like title, notes, due date, status, etc.
    
    Args:
        ctx: FastMCP context
        task_id: The ID of the task to retrieve (required)
        tasklist_id: ID of the task list containing the task (default: "@default")
    
    Returns:
        Dictionary with 'tasklist_id' and 'task' (the complete task object)
    """
    try:
        service = get_google_tasks_service()
        if not service:
            return {"error": "Auth failed"}
        resolved = _resolve_tasklist_id(service, tasklist_id)
        if "error" in resolved:
            return {"error": resolved["error"], **resolved}
        tasklist_id = resolved["tasklist_id"]
        task = service.tasks().get(tasklist=tasklist_id, task=task_id).execute()
        return {"tasklist_id": tasklist_id, "task": task}
    except HttpError as e:
        logger.error(f"Google Tasks API error: {e}")
        return {"error": f"Google Tasks API error: {str(e)}"}
    except Exception as e:
        logger.error(f"Error fetching task: {e}")
        return {"error": str(e)}


@mcp.tool
async def search_tasks(
    ctx: Context,
    tasklist_id: str = "@default",
    query: Optional[str] = None,
    include_completed: bool = False,
    include_deleted: bool = False,
    due_before: Optional[str] = None,
    due_after: Optional[str] = None,
    max_results: int = 100,
) -> dict:
    """
    Search and filter tasks using various criteria.
    
    This function retrieves tasks from the API and applies client-side filtering
    based on the provided criteria. You can search by text, filter by completion
    status, and filter by due date ranges.
    
    Args:
        ctx: FastMCP context
        tasklist_id: ID of the task list to search (default: "@default")
        query: Text to search for in task titles and notes (case-insensitive)
        include_completed: Whether to include completed tasks (default: False)
        include_deleted: Whether to include deleted tasks (default: False)
        due_before: Only return tasks due before this date (RFC 3339 format)
        due_after: Only return tasks due after this date (RFC 3339 format)
        max_results: Maximum number of tasks to retrieve before filtering (default: 100)
    
    Returns:
        Dictionary with 'tasklist_id', 'total' (count of matching tasks), and 'tasks' array
    """
    try:
        service = get_google_tasks_service()
        if not service:
            return {"error": "Auth failed"}
        resolved = _resolve_tasklist_id(service, tasklist_id)
        if "error" in resolved:
            return {"error": resolved["error"], **resolved}
        tasklist_id = resolved["tasklist_id"]

        params: Dict[str, Any] = {
            "tasklist": tasklist_id,
            "maxResults": max_results,
            "showCompleted": include_completed,
            "showDeleted": include_deleted,
        }
        items = service.tasks().list(**params).execute().get("items", [])

        def _match(t: Dict[str, Any]) -> bool:
            if query:
                text = (t.get("title", "") + " " + t.get("notes", "")).lower()
                if query.lower() not in text:
                    return False
            if due_before and t.get("due") and t["due"] > due_before:
                return False
            if due_after and t.get("due") and t["due"] < due_after:
                return False
            return True

        filtered = [t for t in items if _match(t)]
        return {"tasklist_id": tasklist_id, "total": len(filtered), "tasks": filtered}
    except HttpError as e:
        logger.error(f"Google Tasks API error: {e}")
        return {"error": f"Google Tasks API error: {str(e)}"}
    except Exception as e:
        logger.error(f"Error searching tasks: {e}")
        return {"error": str(e)}


@mcp.tool
async def move_task(
    ctx: Context,
    task_id: str,
    tasklist_id: str = "@default",
    parent: Optional[str] = None,
    previous: Optional[str] = None,
) -> dict:
    """
    Move a task to change its position or parent within a task list.
    
    This function allows you to:
    - Reorder tasks by specifying which task to place this one after
    - Create subtask relationships by setting a parent task
    - Move a subtask to become a top-level task by setting parent to null
    
    Args:
        ctx: FastMCP context
        task_id: The ID of the task to move (required)
        tasklist_id: ID of the task list containing the task (default: "@default")
        parent: ID of the parent task to move this under (creates subtask relationship)
        previous: ID of the task that should come before this task (for ordering)
    
    Returns:
        Dictionary with 'tasklist_id' and 'task' (the moved task object with updated position)
    """
    try:
        service = get_google_tasks_service()
        if not service:
            return {"error": "Auth failed"}
        resolved = _resolve_tasklist_id(service, tasklist_id)
        if "error" in resolved:
            return {"error": resolved["error"], **resolved}
        tasklist_id = resolved["tasklist_id"]

        move_kwargs: Dict[str, Any] = {"tasklist": tasklist_id, "task": task_id}
        if parent is not None:
            move_kwargs["parent"] = parent
        if previous is not None:
            move_kwargs["previous"] = previous
        moved = service.tasks().move(**move_kwargs).execute()
        return {"tasklist_id": tasklist_id, "task": moved}
    except HttpError as e:
        logger.error(f"Google Tasks API error: {e}")
        return {"error": f"Google Tasks API error: {str(e)}"}
    except Exception as e:
        logger.error(f"Error moving task: {e}")
        return {"error": str(e)}

def main():
    """Main entry point for the MCP server."""
    logger.info("Starting Google Tasks MCP Server...")
    
    # Run the FastMCP server
    mcp.run()


if __name__ == "__main__":
    main()

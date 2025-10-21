# Google Tasks MCP Server

A comprehensive Model Context Protocol (MCP) server that provides full access to Google Tasks API through FastMCP. Create, read, update, delete, and manage your Google Tasks from any MCP-compatible client.

## Features

### 🔍 **Read Operations**
- **Get Tasks**: Retrieve tasks from Google Tasks with filtering options
- **Get Task**: Fetch a single task by ID
- **List Task Lists**: View all available task lists in your Google account
- **Search Tasks**: Filter tasks by content, due dates, and status

### ✏️ **Write Operations**
- **Create Task**: Add new tasks to any task list
- **Update Task**: Modify existing task properties (title, notes, due date, status)
- **Complete Task**: Mark tasks as completed or incomplete
- **Delete Task**: Remove tasks from task lists
- **Move Task**: Reorder tasks or move them between parent tasks
- **Create Task List**: Create new task lists

### 🔐 **Security & Reliability**
- **OAuth 2.0 Authentication**: Secure token-based authentication with Google
- **Automatic Token Refresh**: Handles token expiration automatically
- **Environment Detection**: Works in both interactive and non-interactive environments
- **Comprehensive Error Handling**: Detailed error messages and logging


## Setup

### 1. Install Dependencies

```bash
# Using uv (recommended)
uv sync

# Or using pip
pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib fastmcp
```

### 2. Google Cloud Console Setup

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Google Tasks API:
   - Go to "APIs & Services" > "Library"
   - Search for "Google Tasks API"
   - Click "Enable"
4. Create credentials:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - Choose "Desktop application"
   - Download the JSON file and save it as `credentials.json` in the project root

### 3. First Run

When you first run the server, it will:
1. Open a browser window for Google authentication
2. Ask you to sign in and grant permissions
3. Save the authentication token for future use

```bash
# Run the server
python main.py

# Or using uv
uv run python main.py
```

## Usage

The server provides **10 comprehensive tools** for managing your Google Tasks:

### 📋 **Task Management Tools**

#### `get_tasks`
Retrieve tasks from a specific task list with filtering options.

**Parameters:**
- `tasklist_id` (string, default: "@default"): ID of the task list
- `max_results` (integer, default: 100): Maximum number of tasks to return
- `show_completed` (boolean, default: false): Include completed tasks
- `show_deleted` (boolean, default: false): Include deleted tasks

#### `get_task`
Fetch a single task by its ID.

**Parameters:**
- `task_id` (string, required): ID of the task to retrieve
- `tasklist_id` (string, default: "@default"): ID of the task list

#### `create_task`
Create a new task in a task list.

**Parameters:**
- `title` (string, required): Title of the new task
- `tasklist_id` (string, default: "@default"): ID of the task list
- `notes` (string, optional): Notes for the task
- `due` (string, optional): Due date in RFC 3339 format
- `parent` (string, optional): ID of parent task for subtasks
- `position` (string, optional): Position to insert the task

#### `update_task`
Update properties of an existing task.

**Parameters:**
- `task_id` (string, required): ID of the task to update
- `tasklist_id` (string, default: "@default"): ID of the task list
- `title` (string, optional): New title
- `notes` (string, optional): New notes
- `due` (string, optional): New due date
- `status` (string, optional): New status ("needsAction" or "completed")
- `parent` (string, optional): New parent task ID
- `position` (string, optional): New position

#### `complete_task`
Mark a task as completed or incomplete.

**Parameters:**
- `task_id` (string, required): ID of the task
- `tasklist_id` (string, default: "@default"): ID of the task list
- `completed` (boolean, default: true): Whether to mark as completed

#### `delete_task`
Delete a task from a task list.

**Parameters:**
- `task_id` (string, required): ID of the task to delete
- `tasklist_id` (string, default: "@default"): ID of the task list

#### `move_task`
Move a task to a new position or reparent it.

**Parameters:**
- `task_id` (string, required): ID of the task to move
- `tasklist_id` (string, default: "@default"): ID of the task list
- `parent` (string, optional): New parent task ID
- `previous` (string, optional): ID of task to place this after

#### `search_tasks`
Search and filter tasks by content and dates.

**Parameters:**
- `tasklist_id` (string, default: "@default"): ID of the task list
- `query` (string, optional): Text to search for in title/notes
- `include_completed` (boolean, default: false): Include completed tasks
- `include_deleted` (boolean, default: false): Include deleted tasks
- `due_before` (string, optional): Filter tasks due before this date
- `due_after` (string, optional): Filter tasks due after this date
- `max_results` (integer, default: 100): Maximum number of results

### 📁 **Task List Management Tools**

#### `list_tasklists`
List all available task lists in your Google account.

**Parameters:** None

#### `create_tasklist`
Create a new task list.

**Parameters:**
- `title` (string, required): Name of the new task list

## MCP Client Integration

### Gemini CLI Configuration

Add to your Gemini settings (`.gemini/settings.json`):

```json
{
  "mcpServers": [
    {
      "name": "google-tasks",
      "command": "uv",
      "args": ["run", "python", "/absolute/path/to/run_server.py"]
    }
  ]
}
```

**Note:** Replace `/absolute/path/to/` with your actual repository path. Alternatively, use `start_server.sh` as the command.

### Example Commands in Gemini CLI

```
@google-tasks list my task lists
@google-tasks get my tasks
@google-tasks create task "Buy groceries" in "My Tasks"
@google-tasks complete task "task-id-here"
@google-tasks search tasks for "meeting"
@google-tasks create tasklist "Work Projects"
```

## Configuration

The server uses the following configuration:

- **Credentials File**: `credentials.json` (downloaded from Google Cloud Console)
- **Token File**: `token.json` (automatically created after first authentication)
- **Scopes**: `https://www.googleapis.com/auth/tasks` (full read/write access)
- **Transport**: STDIO (for MCP protocol communication)

## Error Handling

The server includes comprehensive error handling for:
- Authentication failures
- API rate limits
- Network connectivity issues
- Invalid task list IDs
- Missing credentials

## Testing

### Test the MCP Server Tools

Run the integration test to verify all tools work correctly:

```bash
# Test all MCP tools
uv run python test_all_tools.py

# Test individual server functions
uv run python test_server.py
```

### Test with Gemini

```bash
# Test server directly
python3 run_server.py
```

## Development

To extend the server with additional functionality:

1. Add new tools using the `@mcp.tool` decorator
2. Implement Google Tasks API calls in the tool functions
3. Update the authentication scopes if needed
4. Test with your Google Tasks account
5. Update this README with new tool documentation

### Project Structure

```
google-tasks-mcp-server/
├── server.py              # Main MCP server implementation
├── main.py                # Entry point
├── run_server.py          # Environment wrapper (used by Gemini)
├── start_server.sh        # Shell wrapper for MCP clients
├── test_all_tools.py      # Integration test suite
├── test_server.py         # Unit tests
├── debug_auth.py          # Authentication debugging
├── credentials.json       # Google OAuth credentials (user-provided)
├── token.json            # Authentication token (auto-generated)
└── pyproject.toml        # Dependencies
```

## Security Notes

- Keep your `credentials.json` file secure and never commit it to version control
- The `token.json` file contains your authentication token and should also be kept secure
- The server uses full read/write permissions for Google Tasks (required for create/update/delete operations)
- All API calls are made over HTTPS with OAuth 2.0 authentication

## Troubleshooting

### Common Issues

1. **"Credentials file not found"**: Make sure `credentials.json` is in the project root
2. **"Authentication failed"**: Delete `token.json` and re-authenticate
3. **"Insufficient permissions"**: Delete `token.json` and re-authenticate (scope changed from read-only to read/write)
4. **"No task lists found"**: Make sure you have tasks in your Google Tasks account
5. **"API not enabled"**: Enable the Google Tasks API in Google Cloud Console
6. **"MCP server not found"**: Check your Gemini CLI configuration and server path

### Authentication Issues

If you encounter authentication problems:

```bash
# Delete the old token and re-authenticate
rm token.json
python main.py
# Complete the browser authentication flow
```

### Logs

The server logs important information to help with debugging. Check the console output for detailed error messages.

### Getting Help

- Check the [Google Tasks API documentation](https://developers.google.com/tasks)
- Review the [FastMCP documentation](https://gofastmcp.com)
- Run the test suite to verify functionality: `uv run python test_all_tools.py`

## License

This project is open source and available under the MIT License.

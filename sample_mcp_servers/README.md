# Sample MCP Servers

This directory contains sample MCP (Model Context Protocol) servers for testing SprintConnect functionality.

## Available Servers

### 1. Filesystem Server (`filesystem_server.py`)
- **Purpose**: File system operations for testing
- **Capabilities**: Read/write files, list directories, create directories
- **Tools**: `read_file`, `write_file`, `list_directory`, `create_directory`
- **Resources**: File and directory resources
- **Base Path**: `/tmp/mcp_test` (configurable)

### 2. GitHub Server (`github_server.py`)
- **Purpose**: GitHub operations simulation
- **Capabilities**: Repository info, issue management, repository search
- **Tools**: `get_repo_info`, `list_issues`, `create_issue`, `search_repos`
- **Resources**: GitHub repository and issue resources
- **Mock Data**: Includes sample repositories and issues

### 3. Database Server (`database_server.py`)
- **Purpose**: Database operations using SQLite
- **Capabilities**: SQL query execution, table management, data insertion
- **Tools**: `execute_query`, `list_tables`, `describe_table`, `insert_data`
- **Resources**: Database table resources
- **Database**: SQLite database at `/tmp/mcp_test.db`

## Running the Servers

Each server can be run independently:

```bash
# Filesystem Server
python filesystem_server.py

# GitHub Server
python github_server.py

# Database Server
python database_server.py
```

## Testing with JSON-RPC

All servers accept JSON-RPC requests via stdin. Example:

```json
{"method": "initialize", "params": {"protocolVersion": "2024-11-05"}}
{"method": "tools/list", "params": {}}
{"method": "tools/call", "params": {"name": "read_file", "arguments": {"path": "test.txt"}}}
```

## Integration with SprintConnect

These servers are designed to be registered with SprintConnect and tested through the platform's MCP management features. They implement the MCP protocol specification and provide realistic capabilities for testing:

- Server registration and discovery
- Capability enumeration
- Tool execution
- Resource access
- Health monitoring
- Error handling

## Test Scenarios

The servers support various test scenarios:

### Positive Scenarios
- Successful server initialization
- Tool listing and execution
- Resource access
- Data operations (CRUD)
- Health checks

### Negative Scenarios
- Invalid method calls
- Missing parameters
- Resource not found errors
- Permission errors
- Network connectivity issues

## Configuration

Each server can be configured through constructor parameters:

- **Filesystem Server**: `base_path` for file operations
- **Database Server**: `db_path` for database location
- **GitHub Server**: Mock data can be customized

## Security Considerations

These are test servers and should not be used in production. They include:
- No authentication/authorization
- No input validation beyond basic checks
- Mock data that may not reflect real-world scenarios
- Simplified error handling

## Development

To extend these servers:

1. Add new tools to the `_handle_tools_list()` method
2. Implement tool handlers in `_handle_tool_call()`
3. Add resources to `_handle_resources_list()`
4. Implement resource readers in `_handle_resource_read()`
5. Update server info and capabilities as needed

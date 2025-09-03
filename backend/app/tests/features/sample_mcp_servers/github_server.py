#!/usr/bin/env python3
"""
Sample MCP GitHub Server
Implements GitHub operations for testing SprintConnect
"""

import asyncio
import json
import sys
from typing import Any, Dict, List, Optional

# Add the current directory to Python path for imports
sys.path.insert(0, sys.path[0])

class GitHubMCPServer:
    """Sample MCP server implementing GitHub operations."""
    
    def __init__(self):
        self.server_info = {
            "name": "github-server",
            "version": "1.0.0",
            "description": "Sample GitHub MCP server for testing",
            "capabilities": {
                "tools": ["get_repo_info", "list_issues", "create_issue", "search_repos"],
                "resources": ["github://repos/*", "github://issues/*"]
            }
        }
        # Mock data for testing
        self.mock_repos = {
            "testuser/testrepo": {
                "name": "testrepo",
                "full_name": "testuser/testrepo",
                "description": "A test repository",
                "stars": 42,
                "forks": 5,
                "language": "Python",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-15T12:00:00Z"
            }
        }
        self.mock_issues = {
            "testuser/testrepo": [
                {
                    "number": 1,
                    "title": "Sample Issue",
                    "body": "This is a sample issue for testing",
                    "state": "open",
                    "created_at": "2024-01-10T10:00:00Z",
                    "updated_at": "2024-01-10T10:00:00Z"
                },
                {
                    "number": 2,
                    "title": "Another Issue",
                    "body": "Another sample issue",
                    "state": "closed",
                    "created_at": "2024-01-12T14:00:00Z",
                    "updated_at": "2024-01-14T16:00:00Z"
                }
            ]
        }
    
    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming MCP requests."""
        method = request.get("method")
        params = request.get("params", {})
        
        try:
            if method == "initialize":
                return await self._handle_initialize(params)
            elif method == "tools/list":
                return await self._handle_tools_list()
            elif method == "tools/call":
                return await self._handle_tool_call(params)
            elif method == "resources/list":
                return await self._handle_resources_list()
            elif method == "resources/read":
                return await self._handle_resource_read(params)
            elif method == "ping":
                return {"result": "pong"}
            else:
                return {
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    }
                }
        except Exception as e:
            return {
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }
    
    async def _handle_initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle initialization request."""
        return {
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {"listChanged": True},
                    "resources": {"subscribe": True, "listChanged": True}
                },
                "serverInfo": self.server_info
            }
        }
    
    async def _handle_tools_list(self) -> Dict[str, Any]:
        """List available tools."""
        return {
            "result": {
                "tools": [
                    {
                        "name": "get_repo_info",
                        "description": "Get information about a GitHub repository",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "owner": {
                                    "type": "string",
                                    "description": "Repository owner"
                                },
                                "repo": {
                                    "type": "string",
                                    "description": "Repository name"
                                }
                            },
                            "required": ["owner", "repo"]
                        }
                    },
                    {
                        "name": "list_issues",
                        "description": "List issues for a repository",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "owner": {
                                    "type": "string",
                                    "description": "Repository owner"
                                },
                                "repo": {
                                    "type": "string",
                                    "description": "Repository name"
                                },
                                "state": {
                                    "type": "string",
                                    "description": "Issue state (open, closed, all)",
                                    "default": "open"
                                }
                            },
                            "required": ["owner", "repo"]
                        }
                    },
                    {
                        "name": "create_issue",
                        "description": "Create a new issue",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "owner": {
                                    "type": "string",
                                    "description": "Repository owner"
                                },
                                "repo": {
                                    "type": "string",
                                    "description": "Repository name"
                                },
                                "title": {
                                    "type": "string",
                                    "description": "Issue title"
                                },
                                "body": {
                                    "type": "string",
                                    "description": "Issue body"
                                }
                            },
                            "required": ["owner", "repo", "title"]
                        }
                    },
                    {
                        "name": "search_repos",
                        "description": "Search for repositories",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "query": {
                                    "type": "string",
                                    "description": "Search query"
                                },
                                "language": {
                                    "type": "string",
                                    "description": "Programming language filter"
                                }
                            },
                            "required": ["query"]
                        }
                    }
                ]
            }
        }
    
    async def _handle_tool_call(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tool execution."""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        if tool_name == "get_repo_info":
            return await self._get_repo_info(arguments)
        elif tool_name == "list_issues":
            return await self._list_issues(arguments)
        elif tool_name == "create_issue":
            return await self._create_issue(arguments)
        elif tool_name == "search_repos":
            return await self._search_repos(arguments)
        else:
            return {
                "error": {
                    "code": -32601,
                    "message": f"Tool not found: {tool_name}"
                }
            }
    
    async def _get_repo_info(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get repository information."""
        owner = args.get("owner")
        repo = args.get("repo")
        repo_key = f"{owner}/{repo}"
        
        if repo_key not in self.mock_repos:
            return {
                "error": {
                    "code": -32602,
                    "message": f"Repository not found: {repo_key}"
                }
            }
        
        repo_info = self.mock_repos[repo_key]
        return {
            "result": {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(repo_info, indent=2)
                    }
                ]
            }
        }
    
    async def _list_issues(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """List repository issues."""
        owner = args.get("owner")
        repo = args.get("repo")
        state = args.get("state", "open")
        repo_key = f"{owner}/{repo}"
        
        if repo_key not in self.mock_issues:
            return {
                "error": {
                    "code": -32602,
                    "message": f"Repository not found: {repo_key}"
                }
            }
        
        issues = self.mock_issues[repo_key]
        if state != "all":
            issues = [issue for issue in issues if issue["state"] == state]
        
        return {
            "result": {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(issues, indent=2)
                    }
                ]
            }
        }
    
    async def _create_issue(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new issue."""
        owner = args.get("owner")
        repo = args.get("repo")
        title = args.get("title")
        body = args.get("body", "")
        repo_key = f"{owner}/{repo}"
        
        if repo_key not in self.mock_issues:
            return {
                "error": {
                    "code": -32602,
                    "message": f"Repository not found: {repo_key}"
                }
            }
        
        # Generate new issue number
        existing_issues = self.mock_issues[repo_key]
        new_number = max([issue["number"] for issue in existing_issues], default=0) + 1
        
        new_issue = {
            "number": new_number,
            "title": title,
            "body": body,
            "state": "open",
            "created_at": "2024-01-15T12:00:00Z",
            "updated_at": "2024-01-15T12:00:00Z"
        }
        
        existing_issues.append(new_issue)
        
        return {
            "result": {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(new_issue, indent=2)
                    }
                ]
            }
        }
    
    async def _search_repos(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Search for repositories."""
        query = args.get("query", "")
        language = args.get("language")
        
        # Simple mock search
        results = []
        for repo_key, repo_info in self.mock_repos.items():
            if query.lower() in repo_info["name"].lower() or query.lower() in repo_info["description"].lower():
                if language is None or repo_info["language"].lower() == language.lower():
                    results.append(repo_info)
        
        return {
            "result": {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(results, indent=2)
                    }
                ]
            }
        }
    
    async def _handle_resources_list(self) -> Dict[str, Any]:
        """List available resources."""
        return {
            "result": {
                "resources": [
                    {
                        "uri": "github://repos/testuser/testrepo",
                        "name": "Test Repository",
                        "description": "A test repository for GitHub operations",
                        "mimeType": "application/json"
                    }
                ]
            }
        }
    
    async def _handle_resource_read(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Read a resource."""
        uri = params.get("uri", "")
        
        if uri.startswith("github://repos/"):
            repo_path = uri[15:]  # Remove "github://repos/" prefix
            return await self._get_repo_info({"owner": repo_path.split("/")[0], "repo": repo_path.split("/")[1]})
        elif uri.startswith("github://issues/"):
            # Handle issue resource
            return {
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": "Issue resource content"
                        }
                    ]
                }
            }
        else:
            return {
                "error": {
                    "code": -32602,
                    "message": f"Unsupported resource URI: {uri}"
                }
            }

async def main():
    """Main server loop."""
    server = GitHubMCPServer()
    
    print("GitHub MCP Server starting...")
    print("Server ready. Send JSON-RPC requests to stdin.")
    
    while True:
        try:
            line = await asyncio.get_event_loop().run_in_executor(None, input)
            if not line.strip():
                continue
            
            request = json.loads(line)
            response = await server.handle_request(request)
            print(json.dumps(response))
            
        except json.JSONDecodeError:
            print(json.dumps({
                "error": {
                    "code": -32700,
                    "message": "Parse error"
                }
            }))
        except KeyboardInterrupt:
            print("Server shutting down...")
            break
        except Exception as e:
            print(json.dumps({
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }))

if __name__ == "__main__":
    asyncio.run(main())

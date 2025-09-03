#!/usr/bin/env python3
"""
Sample MCP Filesystem Server
Implements file system operations for testing SprintConnect
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class FilesystemMCPServer:
    """Sample MCP server implementing filesystem operations."""
    
    def __init__(self, base_path: str = "/tmp/mcp_test"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.server_info = {
            "name": "filesystem-server",
            "version": "1.0.0",
            "description": "Sample filesystem MCP server for testing",
            "capabilities": {
                "tools": ["read_file", "write_file", "list_directory", "create_directory"],
                "resources": ["file://*", "directory://*"]
            }
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
                        "name": "read_file",
                        "description": "Read contents of a file",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "path": {
                                    "type": "string",
                                    "description": "Path to the file to read"
                                }
                            },
                            "required": ["path"]
                        }
                    },
                    {
                        "name": "write_file",
                        "description": "Write content to a file",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "path": {
                                    "type": "string",
                                    "description": "Path to the file to write"
                                },
                                "content": {
                                    "type": "string",
                                    "description": "Content to write to the file"
                                }
                            },
                            "required": ["path", "content"]
                        }
                    },
                    {
                        "name": "list_directory",
                        "description": "List contents of a directory",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "path": {
                                    "type": "string",
                                    "description": "Path to the directory to list"
                                }
                            },
                            "required": ["path"]
                        }
                    },
                    {
                        "name": "create_directory",
                        "description": "Create a new directory",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "path": {
                                    "type": "string",
                                    "description": "Path of the directory to create"
                                }
                            },
                            "required": ["path"]
                        }
                    }
                ]
            }
        }
    
    async def _handle_tool_call(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tool execution."""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        if tool_name == "read_file":
            return await self._read_file(arguments)
        elif tool_name == "write_file":
            return await self._write_file(arguments)
        elif tool_name == "list_directory":
            return await self._list_directory(arguments)
        elif tool_name == "create_directory":
            return await self._create_directory(arguments)
        else:
            return {
                "error": {
                    "code": -32601,
                    "message": f"Tool not found: {tool_name}"
                }
            }
    
    async def _read_file(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Read file content."""
        file_path = self.base_path / args["path"]
        
        if not file_path.exists():
            return {
                "error": {
                    "code": -32602,
                    "message": f"File not found: {args['path']}"
                }
            }
        
        try:
            content = file_path.read_text()
            return {
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": content
                        }
                    ]
                }
            }
        except Exception as e:
            return {
                "error": {
                    "code": -32603,
                    "message": f"Error reading file: {str(e)}"
                }
            }
    
    async def _write_file(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Write content to file."""
        file_path = self.base_path / args["path"]
        
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(args["content"])
            return {
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Successfully wrote {len(args['content'])} characters to {args['path']}"
                        }
                    ]
                }
            }
        except Exception as e:
            return {
                "error": {
                    "code": -32603,
                    "message": f"Error writing file: {str(e)}"
                }
            }
    
    async def _list_directory(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """List directory contents."""
        dir_path = self.base_path / args["path"]
        
        if not dir_path.exists():
            return {
                "error": {
                    "code": -32602,
                    "message": f"Directory not found: {args['path']}"
                }
            }
        
        if not dir_path.is_dir():
            return {
                "error": {
                    "code": -32602,
                    "message": f"Path is not a directory: {args['path']}"
                }
            }
        
        try:
            items = []
            for item in dir_path.iterdir():
                items.append({
                    "name": item.name,
                    "type": "directory" if item.is_dir() else "file",
                    "size": item.stat().st_size if item.is_file() else None
                })
            
            return {
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(items, indent=2)
                        }
                    ]
                }
            }
        except Exception as e:
            return {
                "error": {
                    "code": -32603,
                    "message": f"Error listing directory: {str(e)}"
                }
            }
    
    async def _create_directory(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Create a directory."""
        dir_path = self.base_path / args["path"]
        
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
            return {
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Successfully created directory: {args['path']}"
                        }
                    ]
                }
            }
        except Exception as e:
            return {
                "error": {
                    "code": -32603,
                    "message": f"Error creating directory: {str(e)}"
                }
            }
    
    async def _handle_resources_list(self) -> Dict[str, Any]:
        """List available resources."""
        return {
            "result": {
                "resources": [
                    {
                        "uri": f"file://{self.base_path}/",
                        "name": "Root Directory",
                        "description": "Root directory of the filesystem server",
                        "mimeType": "application/x-directory"
                    }
                ]
            }
        }
    
    async def _handle_resource_read(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Read a resource."""
        uri = params.get("uri", "")
        if uri.startswith("file://"):
            file_path = uri[7:]  # Remove "file://" prefix
            return await self._read_file({"path": file_path})
        else:
            return {
                "error": {
                    "code": -32602,
                    "message": f"Unsupported resource URI: {uri}"
                }
            }

async def main():
    """Main server loop."""
    server = FilesystemMCPServer()
    
    print("Filesystem MCP Server starting...")
    print(f"Base path: {server.base_path}")
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

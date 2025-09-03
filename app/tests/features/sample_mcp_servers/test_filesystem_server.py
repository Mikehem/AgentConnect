"""
Test cases for the sample filesystem MCP server.
Tests both positive and negative scenarios for all user stories.
"""

import asyncio
import json
import pytest
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch
import sys
import os

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(__file__))

from filesystem_server import FilesystemMCPServer


class TestFilesystemMCPServer:
    """Test the filesystem MCP server functionality."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir

    @pytest.fixture
    def server(self, temp_dir):
        """Create a filesystem server instance."""
        return FilesystemMCPServer(base_path=temp_dir)

    @pytest.mark.asyncio
    async def test_server_initialization(self, server):
        """Test server initialization (User Story 2.1 - MCP Server Registration)."""
        request = {
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {}
            }
        }
        
        response = await server.handle_request(request)
        
        assert "result" in response
        assert response["result"]["protocolVersion"] == "2024-11-05"
        assert "capabilities" in response["result"]
        assert "serverInfo" in response["result"]
        assert response["result"]["serverInfo"]["name"] == "filesystem-server"

    @pytest.mark.asyncio
    async def test_tools_listing(self, server):
        """Test tools listing (User Story 2.2 - Capability Discovery)."""
        request = {
            "method": "tools/list",
            "params": {}
        }
        
        response = await server.handle_request(request)
        
        assert "result" in response
        assert "tools" in response["result"]
        assert len(response["result"]["tools"]) == 4
        
        tool_names = [tool["name"] for tool in response["result"]["tools"]]
        assert "read_file" in tool_names
        assert "write_file" in tool_names
        assert "list_directory" in tool_names
        assert "create_directory" in tool_names

    @pytest.mark.asyncio
    async def test_write_file_success(self, server):
        """Test successful file writing (User Story 2.3 - Tool Execution)."""
        request = {
            "method": "tools/call",
            "params": {
                "name": "write_file",
                "arguments": {
                    "path": "test.txt",
                    "content": "Hello, World!"
                }
            }
        }
        
        response = await server.handle_request(request)
        
        assert "result" in response
        assert "content" in response["result"]
        assert "Successfully wrote" in response["result"]["content"][0]["text"]
        
        # Verify file was actually created
        file_path = server.base_path / "test.txt"
        assert file_path.exists()
        assert file_path.read_text() == "Hello, World!"

    @pytest.mark.asyncio
    async def test_read_file_success(self, server):
        """Test successful file reading (User Story 2.3 - Tool Execution)."""
        # First create a file
        test_file = server.base_path / "read_test.txt"
        test_file.write_text("Test content")
        
        request = {
            "method": "tools/call",
            "params": {
                "name": "read_file",
                "arguments": {
                    "path": "read_test.txt"
                }
            }
        }
        
        response = await server.handle_request(request)
        
        assert "result" in response
        assert "content" in response["result"]
        assert response["result"]["content"][0]["text"] == "Test content"

    @pytest.mark.asyncio
    async def test_read_file_not_found(self, server):
        """Test reading non-existent file (Negative scenario)."""
        request = {
            "method": "tools/call",
            "params": {
                "name": "read_file",
                "arguments": {
                    "path": "nonexistent.txt"
                }
            }
        }
        
        response = await server.handle_request(request)
        
        assert "error" in response
        assert response["error"]["code"] == -32602
        assert "File not found" in response["error"]["message"]

    @pytest.mark.asyncio
    async def test_create_directory_success(self, server):
        """Test successful directory creation (User Story 2.3 - Tool Execution)."""
        request = {
            "method": "tools/call",
            "params": {
                "name": "create_directory",
                "arguments": {
                    "path": "test_dir"
                }
            }
        }
        
        response = await server.handle_request(request)
        
        assert "result" in response
        assert "Successfully created directory" in response["result"]["content"][0]["text"]
        
        # Verify directory was created
        dir_path = server.base_path / "test_dir"
        assert dir_path.exists()
        assert dir_path.is_dir()

    @pytest.mark.asyncio
    async def test_list_directory_success(self, server):
        """Test successful directory listing (User Story 2.3 - Tool Execution)."""
        # Create test files and directories
        (server.base_path / "file1.txt").write_text("content1")
        (server.base_path / "file2.txt").write_text("content2")
        (server.base_path / "subdir").mkdir()
        
        request = {
            "method": "tools/call",
            "params": {
                "name": "list_directory",
                "arguments": {
                    "path": "."
                }
            }
        }
        
        response = await server.handle_request(request)
        
        assert "result" in response
        content = json.loads(response["result"]["content"][0]["text"])
        
        # Should have at least our test files
        item_names = [item["name"] for item in content]
        assert "file1.txt" in item_names
        assert "file2.txt" in item_names
        assert "subdir" in item_names

    @pytest.mark.asyncio
    async def test_list_directory_not_found(self, server):
        """Test listing non-existent directory (Negative scenario)."""
        request = {
            "method": "tools/call",
            "params": {
                "name": "list_directory",
                "arguments": {
                    "path": "nonexistent_dir"
                }
            }
        }
        
        response = await server.handle_request(request)
        
        assert "error" in response
        assert response["error"]["code"] == -32602
        assert "Directory not found" in response["error"]["message"]

    @pytest.mark.asyncio
    async def test_list_directory_not_a_directory(self, server):
        """Test listing a file as directory (Negative scenario)."""
        # Create a file
        test_file = server.base_path / "test_file.txt"
        test_file.write_text("content")
        
        request = {
            "method": "tools/call",
            "params": {
                "name": "list_directory",
                "arguments": {
                    "path": "test_file.txt"
                }
            }
        }
        
        response = await server.handle_request(request)
        
        assert "error" in response
        assert response["error"]["code"] == -32602
        assert "Path is not a directory" in response["error"]["message"]

    @pytest.mark.asyncio
    async def test_resources_listing(self, server):
        """Test resources listing (User Story 2.2 - Capability Discovery)."""
        request = {
            "method": "resources/list",
            "params": {}
        }
        
        response = await server.handle_request(request)
        
        assert "result" in response
        assert "resources" in response["result"]
        assert len(response["result"]["resources"]) == 1
        assert response["result"]["resources"][0]["uri"].startswith("file://")

    @pytest.mark.asyncio
    async def test_resource_read_success(self, server):
        """Test successful resource reading (User Story 2.3 - Tool Execution)."""
        # Create a test file
        test_file = server.base_path / "resource_test.txt"
        test_file.write_text("Resource content")
        
        request = {
            "method": "resources/read",
            "params": {
                "uri": f"file://{server.base_path}/resource_test.txt"
            }
        }
        
        response = await server.handle_request(request)
        
        assert "result" in response
        assert response["result"]["content"][0]["text"] == "Resource content"

    @pytest.mark.asyncio
    async def test_resource_read_unsupported_uri(self, server):
        """Test reading unsupported resource URI (Negative scenario)."""
        request = {
            "method": "resources/read",
            "params": {
                "uri": "unsupported://test"
            }
        }
        
        response = await server.handle_request(request)
        
        assert "error" in response
        assert response["error"]["code"] == -32602
        assert "Unsupported resource URI" in response["error"]["message"]

    @pytest.mark.asyncio
    async def test_ping_method(self, server):
        """Test ping method (User Story 2.4 - Health Monitoring)."""
        request = {
            "method": "ping",
            "params": {}
        }
        
        response = await server.handle_request(request)
        
        assert "result" in response
        assert response["result"] == "pong"

    @pytest.mark.asyncio
    async def test_invalid_method(self, server):
        """Test invalid method call (Negative scenario)."""
        request = {
            "method": "invalid_method",
            "params": {}
        }
        
        response = await server.handle_request(request)
        
        assert "error" in response
        assert response["error"]["code"] == -32601
        assert "Method not found" in response["error"]["message"]

    @pytest.mark.asyncio
    async def test_missing_tool_arguments(self, server):
        """Test tool call with missing arguments (Negative scenario)."""
        request = {
            "method": "tools/call",
            "params": {
                "name": "read_file",
                "arguments": {}
            }
        }
        
        response = await server.handle_request(request)
        
        assert "error" in response
        assert response["error"]["code"] == -32603

    @pytest.mark.asyncio
    async def test_invalid_tool_name(self, server):
        """Test call to non-existent tool (Negative scenario)."""
        request = {
            "method": "tools/call",
            "params": {
                "name": "nonexistent_tool",
                "arguments": {}
            }
        }
        
        response = await server.handle_request(request)
        
        assert "error" in response
        assert response["error"]["code"] == -32601
        assert "Tool not found" in response["error"]["message"]

    @pytest.mark.asyncio
    async def test_write_file_permission_error(self, server):
        """Test file write permission error (Negative scenario)."""
        # Create a read-only directory
        read_only_dir = server.base_path / "readonly"
        read_only_dir.mkdir()
        read_only_dir.chmod(0o444)  # Read-only
        
        request = {
            "method": "tools/call",
            "params": {
                "name": "write_file",
                "arguments": {
                    "path": "readonly/test.txt",
                    "content": "test"
                }
            }
        }
        
        response = await server.handle_request(request)
        
        # Should get an error due to permission
        assert "error" in response
        assert response["error"]["code"] == -32603
        
        # Clean up
        read_only_dir.chmod(0o755)

    @pytest.mark.asyncio
    async def test_nested_directory_operations(self, server):
        """Test nested directory operations (Complex scenario)."""
        # Create nested directories
        nested_dir = server.base_path / "level1" / "level2" / "level3"
        nested_dir.mkdir(parents=True)
        
        # Write file in nested directory
        request = {
            "method": "tools/call",
            "params": {
                "name": "write_file",
                "arguments": {
                    "path": "level1/level2/level3/nested.txt",
                    "content": "Nested content"
                }
            }
        }
        
        response = await server.handle_request(request)
        
        assert "result" in response
        
        # Read the file back
        request = {
            "method": "tools/call",
            "params": {
                "name": "read_file",
                "arguments": {
                    "path": "level1/level2/level3/nested.txt"
                }
            }
        }
        
        response = await server.handle_request(request)
        
        assert "result" in response
        assert response["result"]["content"][0]["text"] == "Nested content"

    @pytest.mark.asyncio
    async def test_large_file_operations(self, server):
        """Test large file operations (Performance scenario)."""
        large_content = "A" * 10000  # 10KB of data
        
        request = {
            "method": "tools/call",
            "params": {
                "name": "write_file",
                "arguments": {
                    "path": "large_file.txt",
                    "content": large_content
                }
            }
        }
        
        response = await server.handle_request(request)
        
        assert "result" in response
        assert "10000 characters" in response["result"]["content"][0]["text"]
        
        # Read it back
        request = {
            "method": "tools/call",
            "params": {
                "name": "read_file",
                "arguments": {
                    "path": "large_file.txt"
                }
            }
        }
        
        response = await server.handle_request(request)
        
        assert "result" in response
        assert len(response["result"]["content"][0]["text"]) == 10000

    @pytest.mark.asyncio
    async def test_concurrent_operations(self, server):
        """Test concurrent file operations (Concurrency scenario)."""
        async def write_file(filename, content):
            request = {
                "method": "tools/call",
                "params": {
                    "name": "write_file",
                    "arguments": {
                        "path": filename,
                        "content": content
                    }
                }
            }
            return await server.handle_request(request)
        
        # Run multiple write operations concurrently
        tasks = [
            write_file(f"concurrent_{i}.txt", f"Content {i}")
            for i in range(5)
        ]
        
        responses = await asyncio.gather(*tasks)
        
        # All should succeed
        for response in responses:
            assert "result" in response
        
        # Verify all files were created
        for i in range(5):
            file_path = server.base_path / f"concurrent_{i}.txt"
            assert file_path.exists()
            assert file_path.read_text() == f"Content {i}"

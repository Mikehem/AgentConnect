"""
Integration tests for sample MCP servers with SprintConnect.
Tests all user stories with real MCP server interactions.
"""

import asyncio
import json
import pytest
import tempfile
import subprocess
import time
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock
import sys
import os
import httpx

# Add the sample_mcp_servers directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../../sample_mcp_servers'))

from filesystem_server import FilesystemMCPServer
from github_server import GitHubMCPServer
from database_server import DatabaseMCPServer


class TestSprintConnectIntegration:
    """Test integration between SprintConnect and sample MCP servers."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database file for testing."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_file:
            temp_path = temp_file.name
        yield temp_path
        # Clean up
        Path(temp_path).unlink(missing_ok=True)

    @pytest.fixture
    def sample_servers(self, temp_dir, temp_db):
        """Create sample MCP server instances."""
        return {
            "filesystem": FilesystemMCPServer(base_path=temp_dir),
            "github": GitHubMCPServer(),
            "database": DatabaseMCPServer(db_path=temp_db)
        }

    @pytest.mark.asyncio
    async def test_user_story_2_1_server_registration(self, sample_servers):
        """Test User Story 2.1: MCP Server Registration with sample servers."""
        # Test each server can be initialized (simulating registration)
        for server_name, server in sample_servers.items():
            request = {
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {}
                }
            }
            
            response = await server.handle_request(request)
            
            assert "result" in response, f"Server {server_name} failed to initialize"
            assert response["result"]["protocolVersion"] == "2024-11-05"
            assert "serverInfo" in response["result"]
            assert "capabilities" in response["result"]
            
            # Verify server info contains expected fields
            server_info = response["result"]["serverInfo"]
            assert "name" in server_info
            assert "version" in server_info
            assert "description" in server_info
            assert "capabilities" in server_info

    @pytest.mark.asyncio
    async def test_user_story_2_2_capability_discovery(self, sample_servers):
        """Test User Story 2.2: Capability Discovery with sample servers."""
        for server_name, server in sample_servers.items():
            # Test tools listing
            tools_request = {
                "method": "tools/list",
                "params": {}
            }
            
            tools_response = await server.handle_request(tools_request)
            
            assert "result" in tools_response, f"Server {server_name} failed to list tools"
            assert "tools" in tools_response["result"]
            assert len(tools_response["result"]["tools"]) > 0
            
            # Verify each tool has required fields
            for tool in tools_response["result"]["tools"]:
                assert "name" in tool
                assert "description" in tool
                assert "inputSchema" in tool
            
            # Test resources listing
            resources_request = {
                "method": "resources/list",
                "params": {}
            }
            
            resources_response = await server.handle_request(resources_request)
            
            assert "result" in resources_response, f"Server {server_name} failed to list resources"
            assert "resources" in resources_response["result"]
            
            # Verify each resource has required fields
            for resource in resources_response["result"]["resources"]:
                assert "uri" in resource
                assert "name" in resource
                assert "description" in resource

    @pytest.mark.asyncio
    async def test_user_story_2_3_tool_execution_filesystem(self, sample_servers):
        """Test User Story 2.3: Tool Execution with filesystem server."""
        server = sample_servers["filesystem"]
        
        # Test file operations workflow
        # 1. Create directory
        create_dir_request = {
            "method": "tools/call",
            "params": {
                "name": "create_directory",
                "arguments": {
                    "path": "test_workflow"
                }
            }
        }
        
        response = await server.handle_request(create_dir_request)
        assert "result" in response
        
        # 2. Write file
        write_file_request = {
            "method": "tools/call",
            "params": {
                "name": "write_file",
                "arguments": {
                    "path": "test_workflow/sample.txt",
                    "content": "Hello from SprintConnect integration test!"
                }
            }
        }
        
        response = await server.handle_request(write_file_request)
        assert "result" in response
        
        # 3. Read file
        read_file_request = {
            "method": "tools/call",
            "params": {
                "name": "read_file",
                "arguments": {
                    "path": "test_workflow/sample.txt"
                }
            }
        }
        
        response = await server.handle_request(read_file_request)
        assert "result" in response
        assert "Hello from SprintConnect integration test!" in response["result"]["content"][0]["text"]
        
        # 4. List directory
        list_dir_request = {
            "method": "tools/call",
            "params": {
                "name": "list_directory",
                "arguments": {
                    "path": "test_workflow"
                }
            }
        }
        
        response = await server.handle_request(list_dir_request)
        assert "result" in response
        
        directory_contents = json.loads(response["result"]["content"][0]["text"])
        assert len(directory_contents) == 1
        assert directory_contents[0]["name"] == "sample.txt"

    @pytest.mark.asyncio
    async def test_user_story_2_3_tool_execution_github(self, sample_servers):
        """Test User Story 2.3: Tool Execution with GitHub server."""
        server = sample_servers["github"]
        
        # Test GitHub operations workflow
        # 1. Get repository info
        repo_info_request = {
            "method": "tools/call",
            "params": {
                "name": "get_repo_info",
                "arguments": {
                    "owner": "testuser",
                    "repo": "testrepo"
                }
            }
        }
        
        response = await server.handle_request(repo_info_request)
        assert "result" in response
        
        repo_info = json.loads(response["result"]["content"][0]["text"])
        assert repo_info["name"] == "testrepo"
        assert repo_info["full_name"] == "testuser/testrepo"
        
        # 2. List issues
        list_issues_request = {
            "method": "tools/call",
            "params": {
                "name": "list_issues",
                "arguments": {
                    "owner": "testuser",
                    "repo": "testrepo",
                    "state": "open"
                }
            }
        }
        
        response = await server.handle_request(list_issues_request)
        assert "result" in response
        
        issues = json.loads(response["result"]["content"][0]["text"])
        assert len(issues) > 0
        
        # 3. Create new issue
        create_issue_request = {
            "method": "tools/call",
            "params": {
                "name": "create_issue",
                "arguments": {
                    "owner": "testuser",
                    "repo": "testrepo",
                    "title": "Integration Test Issue",
                    "body": "This issue was created during SprintConnect integration testing"
                }
            }
        }
        
        response = await server.handle_request(create_issue_request)
        assert "result" in response
        
        new_issue = json.loads(response["result"]["content"][0]["text"])
        assert new_issue["title"] == "Integration Test Issue"
        assert new_issue["state"] == "open"
        
        # 4. Search repositories
        search_repos_request = {
            "method": "tools/call",
            "params": {
                "name": "search_repos",
                "arguments": {
                    "query": "test",
                    "language": "Python"
                }
            }
        }
        
        response = await server.handle_request(search_repos_request)
        assert "result" in response
        
        repos = json.loads(response["result"]["content"][0]["text"])
        assert len(repos) > 0
        assert repos[0]["language"] == "Python"

    @pytest.mark.asyncio
    async def test_user_story_2_3_tool_execution_database(self, sample_servers):
        """Test User Story 2.3: Tool Execution with database server."""
        server = sample_servers["database"]
        
        # Test database operations workflow
        # 1. List tables
        list_tables_request = {
            "method": "tools/call",
            "params": {
                "name": "list_tables",
                "arguments": {}
            }
        }
        
        response = await server.handle_request(list_tables_request)
        assert "result" in response
        
        tables = json.loads(response["result"]["content"][0]["text"])
        assert "users" in tables
        assert "products" in tables
        
        # 2. Describe table
        describe_table_request = {
            "method": "tools/call",
            "params": {
                "name": "describe_table",
                "arguments": {
                    "table_name": "users"
                }
            }
        }
        
        response = await server.handle_request(describe_table_request)
        assert "result" in response
        
        schema = json.loads(response["result"]["content"][0]["text"])
        assert len(schema) > 0
        
        # 3. Insert data
        insert_data_request = {
            "method": "tools/call",
            "params": {
                "name": "insert_data",
                "arguments": {
                    "table": "users",
                    "data": {
                        "name": "Integration Test User",
                        "email": "integration@example.com"
                    }
                }
            }
        }
        
        response = await server.handle_request(insert_data_request)
        assert "result" in response
        
        # 4. Query data
        query_request = {
            "method": "tools/call",
            "params": {
                "name": "execute_query",
                "arguments": {
                    "query": "SELECT * FROM users WHERE name = 'Integration Test User'"
                }
            }
        }
        
        response = await server.handle_request(query_request)
        assert "result" in response
        
        results = json.loads(response["result"]["content"][0]["text"])
        assert len(results) == 1
        assert results[0]["name"] == "Integration Test User"
        assert results[0]["email"] == "integration@example.com"

    @pytest.mark.asyncio
    async def test_user_story_2_4_health_monitoring(self, sample_servers):
        """Test User Story 2.4: Health Monitoring with sample servers."""
        for server_name, server in sample_servers.items():
            # Test ping method
            ping_request = {
                "method": "ping",
                "params": {}
            }
            
            response = await server.handle_request(ping_request)
            
            assert "result" in response, f"Server {server_name} failed ping test"
            assert response["result"] == "pong"
            
            # Test server can handle multiple requests (performance test)
            start_time = time.time()
            
            for _ in range(10):
                response = await server.handle_request(ping_request)
                assert "result" in response
            
            end_time = time.time()
            duration = end_time - start_time
            
            # Should complete 10 pings in reasonable time (less than 1 second)
            assert duration < 1.0, f"Server {server_name} performance test failed"

    @pytest.mark.asyncio
    async def test_user_story_2_5_resource_access(self, sample_servers):
        """Test User Story 2.5: Resource Access with sample servers."""
        # Test filesystem resource access
        fs_server = sample_servers["filesystem"]
        
        # Create a test file first
        write_request = {
            "method": "tools/call",
            "params": {
                "name": "write_file",
                "arguments": {
                    "path": "resource_test.txt",
                    "content": "Resource access test content"
                }
            }
        }
        
        response = await fs_server.handle_request(write_request)
        assert "result" in response
        
        # Read as resource
        resource_request = {
            "method": "resources/read",
            "params": {
                "uri": f"file://{fs_server.base_path}/resource_test.txt"
            }
        }
        
        response = await fs_server.handle_request(resource_request)
        assert "result" in response
        assert "Resource access test content" in response["result"]["content"][0]["text"]
        
        # Test GitHub resource access
        github_server = sample_servers["github"]
        
        resource_request = {
            "method": "resources/read",
            "params": {
                "uri": "github://repos/testuser/testrepo"
            }
        }
        
        response = await github_server.handle_request(resource_request)
        assert "result" in response
        
        repo_info = json.loads(response["result"]["content"][0]["text"])
        assert repo_info["name"] == "testrepo"
        
        # Test database resource access
        db_server = sample_servers["database"]
        
        resource_request = {
            "method": "resources/read",
            "params": {
                "uri": "db://tables/users"
            }
        }
        
        response = await db_server.handle_request(resource_request)
        assert "result" in response
        
        results = json.loads(response["result"]["content"][0]["text"])
        assert len(results) > 0

    @pytest.mark.asyncio
    async def test_error_handling_scenarios(self, sample_servers):
        """Test error handling across all sample servers."""
        # Test invalid method
        for server_name, server in sample_servers.items():
            invalid_request = {
                "method": "invalid_method",
                "params": {}
            }
            
            response = await server.handle_request(invalid_request)
            
            assert "error" in response, f"Server {server_name} should return error for invalid method"
            assert response["error"]["code"] == -32601
            assert "Method not found" in response["error"]["message"]
        
        # Test missing arguments
        fs_server = sample_servers["filesystem"]
        
        missing_args_request = {
            "method": "tools/call",
            "params": {
                "name": "read_file",
                "arguments": {}
            }
        }
        
        response = await fs_server.handle_request(missing_args_request)
        assert "error" in response
        assert response["error"]["code"] == -32603
        
        # Test non-existent resource
        github_server = sample_servers["github"]
        
        nonexistent_repo_request = {
            "method": "tools/call",
            "params": {
                "name": "get_repo_info",
                "arguments": {
                    "owner": "nonexistent",
                    "repo": "repo"
                }
            }
        }
        
        response = await github_server.handle_request(nonexistent_repo_request)
        assert "error" in response
        assert response["error"]["code"] == -32603
        assert "Repository not found" in response["error"]["message"]

    @pytest.mark.asyncio
    async def test_concurrent_operations(self, sample_servers):
        """Test concurrent operations across multiple servers."""
        async def perform_operation(server, operation_name):
            """Perform a specific operation on a server."""
            if operation_name == "ping":
                request = {"method": "ping", "params": {}}
            elif operation_name == "list_tools":
                request = {"method": "tools/list", "params": {}}
            elif operation_name == "list_resources":
                request = {"method": "resources/list", "params": {}}
            else:
                return None
            
            return await server.handle_request(request)
        
        # Run concurrent operations across all servers
        tasks = []
        for server_name, server in sample_servers.items():
            tasks.extend([
                perform_operation(server, "ping"),
                perform_operation(server, "list_tools"),
                perform_operation(server, "list_resources")
            ])
        
        responses = await asyncio.gather(*tasks)
        
        # All operations should succeed
        for response in responses:
            assert response is not None
            assert "result" in response or "error" in response

    @pytest.mark.asyncio
    async def test_complex_workflow_integration(self, sample_servers):
        """Test complex workflow involving multiple servers."""
        # 1. Create a file with filesystem server
        fs_server = sample_servers["filesystem"]
        
        write_request = {
            "method": "tools/call",
            "params": {
                "name": "write_file",
                "arguments": {
                    "path": "workflow_data.json",
                    "content": json.dumps({
                        "project": "SprintConnect Integration Test",
                        "status": "in_progress",
                        "created_by": "test_user"
                    })
                }
            }
        }
        
        response = await fs_server.handle_request(write_request)
        assert "result" in response
        
        # 2. Read the file back
        read_request = {
            "method": "tools/call",
            "params": {
                "name": "read_file",
                "arguments": {
                    "path": "workflow_data.json"
                }
            }
        }
        
        response = await fs_server.handle_request(read_request)
        assert "result" in response
        
        data = json.loads(response["result"]["content"][0]["text"])
        assert data["project"] == "SprintConnect Integration Test"
        
        # 3. Create a GitHub issue about the workflow
        github_server = sample_servers["github"]
        
        issue_request = {
            "method": "tools/call",
            "params": {
                "name": "create_issue",
                "arguments": {
                    "owner": "testuser",
                    "repo": "testrepo",
                    "title": f"Workflow Test - {data['project']}",
                    "body": f"Testing complex workflow integration. Status: {data['status']}"
                }
            }
        }
        
        response = await github_server.handle_request(issue_request)
        assert "result" in response
        
        issue = json.loads(response["result"]["content"][0]["text"])
        assert "Workflow Test" in issue["title"]
        
        # 4. Store workflow metadata in database
        db_server = sample_servers["database"]
        
        # First, create a workflow_logs table
        create_table_request = {
            "method": "tools/call",
            "params": {
                "name": "execute_query",
                "arguments": {
                    "query": "CREATE TABLE IF NOT EXISTS workflow_logs (id INTEGER PRIMARY KEY, project TEXT, status TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"
                }
            }
        }
        
        response = await db_server.handle_request(create_table_request)
        assert "result" in response
        
        # Insert workflow log
        insert_request = {
            "method": "tools/call",
            "params": {
                "name": "execute_query",
                "arguments": {
                    "query": f"INSERT INTO workflow_logs (project, status) VALUES ('{data['project']}', '{data['status']}')"
                }
            }
        }
        
        response = await db_server.handle_request(insert_request)
        assert "result" in response
        
        # 5. Verify the complete workflow
        verify_request = {
            "method": "tools/call",
            "params": {
                "name": "execute_query",
                "arguments": {
                    "query": "SELECT * FROM workflow_logs WHERE project = 'SprintConnect Integration Test'"
                }
            }
        }
        
        response = await db_server.handle_request(verify_request)
        assert "result" in response
        
        logs = json.loads(response["result"]["content"][0]["text"])
        assert len(logs) == 1
        assert logs[0]["project"] == "SprintConnect Integration Test"
        assert logs[0]["status"] == "in_progress"

    @pytest.mark.asyncio
    async def test_performance_benchmarks(self, sample_servers):
        """Test performance benchmarks for sample servers."""
        for server_name, server in sample_servers.items():
            # Benchmark ping operations
            start_time = time.time()
            
            for _ in range(100):
                request = {"method": "ping", "params": {}}
                response = await server.handle_request(request)
                assert "result" in response
            
            end_time = time.time()
            duration = end_time - start_time
            
            # Should complete 100 pings in reasonable time
            assert duration < 5.0, f"Server {server_name} ping benchmark failed: {duration}s for 100 operations"
            
            # Calculate operations per second
            ops_per_second = 100 / duration
            print(f"{server_name} server: {ops_per_second:.2f} operations/second")

    @pytest.mark.asyncio
    async def test_memory_usage_stability(self, sample_servers):
        """Test memory usage stability during extended operations."""
        for server_name, server in sample_servers.items():
            # Perform many operations to test memory stability
            for i in range(1000):
                request = {"method": "ping", "params": {}}
                response = await server.handle_request(request)
                assert "result" in response
                
                # Every 100 operations, test a more complex operation
                if i % 100 == 0:
                    if server_name == "filesystem":
                        complex_request = {
                            "method": "tools/call",
                            "params": {
                                "name": "list_directory",
                                "arguments": {"path": "."}
                            }
                        }
                    elif server_name == "github":
                        complex_request = {
                            "method": "tools/call",
                            "params": {
                                "name": "list_issues",
                                "arguments": {
                                    "owner": "testuser",
                                    "repo": "testrepo",
                                    "state": "all"
                                }
                            }
                        }
                    elif server_name == "database":
                        complex_request = {
                            "method": "tools/call",
                            "params": {
                                "name": "list_tables",
                                "arguments": {}
                            }
                        }
                    
                    response = await server.handle_request(complex_request)
                    assert "result" in response

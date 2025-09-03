"""
Test cases for the sample GitHub MCP server.
Tests both positive and negative scenarios for all user stories.
"""

import asyncio
import json
import pytest
from unittest.mock import AsyncMock, patch
import sys
import os

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(__file__))

from github_server import GitHubMCPServer


class TestGitHubMCPServer:
    """Test the GitHub MCP server functionality."""

    @pytest.fixture
    def server(self):
        """Create a GitHub server instance."""
        return GitHubMCPServer()

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
        assert response["result"]["serverInfo"]["name"] == "github-server"

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
        assert "get_repo_info" in tool_names
        assert "list_issues" in tool_names
        assert "create_issue" in tool_names
        assert "search_repos" in tool_names

    @pytest.mark.asyncio
    async def test_get_repo_info_success(self, server):
        """Test successful repository info retrieval (User Story 2.3 - Tool Execution)."""
        request = {
            "method": "tools/call",
            "params": {
                "name": "get_repo_info",
                "arguments": {
                    "owner": "testuser",
                    "repo": "testrepo"
                }
            }
        }
        
        response = await server.handle_request(request)
        
        assert "result" in response
        assert "content" in response["result"]
        
        repo_info = json.loads(response["result"]["content"][0]["text"])
        assert repo_info["name"] == "testrepo"
        assert repo_info["full_name"] == "testuser/testrepo"
        assert repo_info["stars"] == 42
        assert repo_info["language"] == "Python"

    @pytest.mark.asyncio
    async def test_get_repo_info_not_found(self, server):
        """Test repository info for non-existent repo (Negative scenario)."""
        request = {
            "method": "tools/call",
            "params": {
                "name": "get_repo_info",
                "arguments": {
                    "owner": "nonexistent",
                    "repo": "repo"
                }
            }
        }
        
        response = await server.handle_request(request)
        
        assert "error" in response
        assert response["error"]["code"] == -32602
        assert "Repository not found" in response["error"]["message"]

    @pytest.mark.asyncio
    async def test_list_issues_success(self, server):
        """Test successful issue listing (User Story 2.3 - Tool Execution)."""
        request = {
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
        
        response = await server.handle_request(request)
        
        assert "result" in response
        assert "content" in response["result"]
        
        issues = json.loads(response["result"]["content"][0]["text"])
        assert len(issues) == 1  # Only open issues
        assert issues[0]["state"] == "open"
        assert issues[0]["title"] == "Sample Issue"

    @pytest.mark.asyncio
    async def test_list_issues_all_states(self, server):
        """Test listing all issues regardless of state (User Story 2.3 - Tool Execution)."""
        request = {
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
        
        response = await server.handle_request(request)
        
        assert "result" in response
        assert "content" in response["result"]
        
        issues = json.loads(response["result"]["content"][0]["text"])
        assert len(issues) == 2  # Both open and closed issues
        states = [issue["state"] for issue in issues]
        assert "open" in states
        assert "closed" in states

    @pytest.mark.asyncio
    async def test_list_issues_repo_not_found(self, server):
        """Test listing issues for non-existent repo (Negative scenario)."""
        request = {
            "method": "tools/call",
            "params": {
                "name": "list_issues",
                "arguments": {
                    "owner": "nonexistent",
                    "repo": "repo"
                }
            }
        }
        
        response = await server.handle_request(request)
        
        assert "error" in response
        assert response["error"]["code"] == -32602
        assert "Repository not found" in response["error"]["message"]

    @pytest.mark.asyncio
    async def test_create_issue_success(self, server):
        """Test successful issue creation (User Story 2.3 - Tool Execution)."""
        request = {
            "method": "tools/call",
            "params": {
                "name": "create_issue",
                "arguments": {
                    "owner": "testuser",
                    "repo": "testrepo",
                    "title": "New Test Issue",
                    "body": "This is a test issue created via MCP"
                }
            }
        }
        
        response = await server.handle_request(request)
        
        assert "result" in response
        assert "content" in response["result"]
        
        issue = json.loads(response["result"]["content"][0]["text"])
        assert issue["title"] == "New Test Issue"
        assert issue["body"] == "This is a test issue created via MCP"
        assert issue["state"] == "open"
        assert issue["number"] == 3  # Should be the next number

    @pytest.mark.asyncio
    async def test_create_issue_minimal(self, server):
        """Test issue creation with minimal required fields (User Story 2.3 - Tool Execution)."""
        request = {
            "method": "tools/call",
            "params": {
                "name": "create_issue",
                "arguments": {
                    "owner": "testuser",
                    "repo": "testrepo",
                    "title": "Minimal Issue"
                }
            }
        }
        
        response = await server.handle_request(request)
        
        assert "result" in response
        assert "content" in response["result"]
        
        issue = json.loads(response["result"]["content"][0]["text"])
        assert issue["title"] == "Minimal Issue"
        assert issue["body"] == ""  # Should default to empty string
        assert issue["state"] == "open"

    @pytest.mark.asyncio
    async def test_create_issue_repo_not_found(self, server):
        """Test creating issue in non-existent repo (Negative scenario)."""
        request = {
            "method": "tools/call",
            "params": {
                "name": "create_issue",
                "arguments": {
                    "owner": "nonexistent",
                    "repo": "repo",
                    "title": "Test Issue"
                }
            }
        }
        
        response = await server.handle_request(request)
        
        assert "error" in response
        assert response["error"]["code"] == -32602
        assert "Repository not found" in response["error"]["message"]

    @pytest.mark.asyncio
    async def test_search_repos_success(self, server):
        """Test successful repository search (User Story 2.3 - Tool Execution)."""
        request = {
            "method": "tools/call",
            "params": {
                "name": "search_repos",
                "arguments": {
                    "query": "test"
                }
            }
        }
        
        response = await server.handle_request(request)
        
        assert "result" in response
        assert "content" in response["result"]
        
        repos = json.loads(response["result"]["content"][0]["text"])
        assert len(repos) == 1
        assert repos[0]["name"] == "testrepo"

    @pytest.mark.asyncio
    async def test_search_repos_with_language_filter(self, server):
        """Test repository search with language filter (User Story 2.3 - Tool Execution)."""
        request = {
            "method": "tools/call",
            "params": {
                "name": "search_repos",
                "arguments": {
                    "query": "test",
                    "language": "Python"
                }
            }
        }
        
        response = await server.handle_request(request)
        
        assert "result" in response
        assert "content" in response["result"]
        
        repos = json.loads(response["result"]["content"][0]["text"])
        assert len(repos) == 1
        assert repos[0]["language"] == "Python"

    @pytest.mark.asyncio
    async def test_search_repos_no_results(self, server):
        """Test repository search with no results (Negative scenario)."""
        request = {
            "method": "tools/call",
            "params": {
                "name": "search_repos",
                "arguments": {
                    "query": "nonexistent"
                }
            }
        }
        
        response = await server.handle_request(request)
        
        assert "result" in response
        assert "content" in response["result"]
        
        repos = json.loads(response["result"]["content"][0]["text"])
        assert len(repos) == 0

    @pytest.mark.asyncio
    async def test_search_repos_language_filter_no_match(self, server):
        """Test repository search with language filter that doesn't match (Negative scenario)."""
        request = {
            "method": "tools/call",
            "params": {
                "name": "search_repos",
                "arguments": {
                    "query": "test",
                    "language": "JavaScript"
                }
            }
        }
        
        response = await server.handle_request(request)
        
        assert "result" in response
        assert "content" in response["result"]
        
        repos = json.loads(response["result"]["content"][0]["text"])
        assert len(repos) == 0

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
        assert response["result"]["resources"][0]["uri"] == "github://repos/testuser/testrepo"

    @pytest.mark.asyncio
    async def test_resource_read_repo_success(self, server):
        """Test successful repository resource reading (User Story 2.3 - Tool Execution)."""
        request = {
            "method": "resources/read",
            "params": {
                "uri": "github://repos/testuser/testrepo"
            }
        }
        
        response = await server.handle_request(request)
        
        assert "result" in response
        assert "content" in response["result"]
        
        repo_info = json.loads(response["result"]["content"][0]["text"])
        assert repo_info["name"] == "testrepo"
        assert repo_info["full_name"] == "testuser/testrepo"

    @pytest.mark.asyncio
    async def test_resource_read_issue_success(self, server):
        """Test successful issue resource reading (User Story 2.3 - Tool Execution)."""
        request = {
            "method": "resources/read",
            "params": {
                "uri": "github://issues/testuser/testrepo/1"
            }
        }
        
        response = await server.handle_request(request)
        
        assert "result" in response
        assert "content" in response["result"]
        assert "Issue resource content" in response["result"]["content"][0]["text"]

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
        """Test tool call with missing required arguments (Negative scenario)."""
        request = {
            "method": "tools/call",
            "params": {
                "name": "get_repo_info",
                "arguments": {
                    "owner": "testuser"
                    # Missing "repo" argument
                }
            }
        }
        
        response = await server.handle_request(request)
        
        assert "error" in response
        assert response["error"]["code"] == -32602

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
    async def test_multiple_issue_creation(self, server):
        """Test creating multiple issues and verifying numbering (Complex scenario)."""
        # Create first issue
        request1 = {
            "method": "tools/call",
            "params": {
                "name": "create_issue",
                "arguments": {
                    "owner": "testuser",
                    "repo": "testrepo",
                    "title": "Issue 1"
                }
            }
        }
        
        response1 = await server.handle_request(request1)
        assert "result" in response1
        issue1 = json.loads(response1["result"]["content"][0]["text"])
        assert issue1["number"] == 3  # Should be next number after existing issues
        
        # Create second issue
        request2 = {
            "method": "tools/call",
            "params": {
                "name": "create_issue",
                "arguments": {
                    "owner": "testuser",
                    "repo": "testrepo",
                    "title": "Issue 2"
                }
            }
        }
        
        response2 = await server.handle_request(request2)
        assert "result" in response2
        issue2 = json.loads(response2["result"]["content"][0]["text"])
        assert issue2["number"] == 4  # Should be next number
        
        # Verify both issues are in the list
        request3 = {
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
        
        response3 = await server.handle_request(request3)
        assert "result" in response3
        issues = json.loads(response3["result"]["content"][0]["text"])
        assert len(issues) == 4  # Original 2 + 2 new ones
        
        issue_numbers = [issue["number"] for issue in issues]
        assert 3 in issue_numbers
        assert 4 in issue_numbers

    @pytest.mark.asyncio
    async def test_case_insensitive_search(self, server):
        """Test case-insensitive repository search (Complex scenario)."""
        # Test with uppercase query
        request = {
            "method": "tools/call",
            "params": {
                "name": "search_repos",
                "arguments": {
                    "query": "TEST"
                }
            }
        }
        
        response = await server.handle_request(request)
        
        assert "result" in response
        repos = json.loads(response["result"]["content"][0]["text"])
        assert len(repos) == 1
        assert repos[0]["name"] == "testrepo"

    @pytest.mark.asyncio
    async def test_concurrent_operations(self, server):
        """Test concurrent GitHub operations (Concurrency scenario)."""
        async def create_issue(title):
            request = {
                "method": "tools/call",
                "params": {
                    "name": "create_issue",
                    "arguments": {
                        "owner": "testuser",
                        "repo": "testrepo",
                        "title": title
                    }
                }
            }
            return await server.handle_request(request)
        
        # Run multiple issue creation operations concurrently
        tasks = [
            create_issue(f"Concurrent Issue {i}")
            for i in range(3)
        ]
        
        responses = await asyncio.gather(*tasks)
        
        # All should succeed
        for response in responses:
            assert "result" in response
        
        # Verify all issues were created with unique numbers
        issue_numbers = []
        for response in responses:
            issue = json.loads(response["result"]["content"][0]["text"])
            issue_numbers.append(issue["number"])
        
        # Should have unique numbers
        assert len(set(issue_numbers)) == len(issue_numbers)

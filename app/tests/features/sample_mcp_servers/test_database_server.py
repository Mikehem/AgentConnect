"""
Test cases for the sample database MCP server.
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

from database_server import DatabaseMCPServer


class TestDatabaseMCPServer:
    """Test the database MCP server functionality."""

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database file for testing."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_file:
            temp_path = temp_file.name
        yield temp_path
        # Clean up
        Path(temp_path).unlink(missing_ok=True)

    @pytest.fixture
    def server(self, temp_db):
        """Create a database server instance."""
        return DatabaseMCPServer(db_path=temp_db)

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
        assert response["result"]["serverInfo"]["name"] == "database-server"

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
        assert "execute_query" in tool_names
        assert "list_tables" in tool_names
        assert "describe_table" in tool_names
        assert "insert_data" in tool_names

    @pytest.mark.asyncio
    async def test_list_tables_success(self, server):
        """Test successful table listing (User Story 2.3 - Tool Execution)."""
        request = {
            "method": "tools/call",
            "params": {
                "name": "list_tables",
                "arguments": {}
            }
        }
        
        response = await server.handle_request(request)
        
        assert "result" in response
        assert "content" in response["result"]
        
        tables = json.loads(response["result"]["content"][0]["text"])
        assert "users" in tables
        assert "products" in tables

    @pytest.mark.asyncio
    async def test_describe_table_success(self, server):
        """Test successful table description (User Story 2.3 - Tool Execution)."""
        request = {
            "method": "tools/call",
            "params": {
                "name": "describe_table",
                "arguments": {
                    "table_name": "users"
                }
            }
        }
        
        response = await server.handle_request(request)
        
        assert "result" in response
        assert "content" in response["result"]
        
        schema = json.loads(response["result"]["content"][0]["text"])
        assert len(schema) > 0
        
        # Check for expected columns
        column_names = [col["name"] for col in schema]
        assert "id" in column_names
        assert "name" in column_names
        assert "email" in column_names
        assert "created_at" in column_names

    @pytest.mark.asyncio
    async def test_describe_table_not_found(self, server):
        """Test describing non-existent table (Negative scenario)."""
        request = {
            "method": "tools/call",
            "params": {
                "name": "describe_table",
                "arguments": {
                    "table_name": "nonexistent_table"
                }
            }
        }
        
        response = await server.handle_request(request)
        
        assert "error" in response
        assert response["error"]["code"] == -32602
        assert "Table not found" in response["error"]["message"]

    @pytest.mark.asyncio
    async def test_execute_query_select_success(self, server):
        """Test successful SELECT query execution (User Story 2.3 - Tool Execution)."""
        request = {
            "method": "tools/call",
            "params": {
                "name": "execute_query",
                "arguments": {
                    "query": "SELECT * FROM users LIMIT 1"
                }
            }
        }
        
        response = await server.handle_request(request)
        
        assert "result" in response
        assert "content" in response["result"]
        
        results = json.loads(response["result"]["content"][0]["text"])
        assert len(results) == 1
        assert "name" in results[0]
        assert "email" in results[0]

    @pytest.mark.asyncio
    async def test_execute_query_insert_success(self, server):
        """Test successful INSERT query execution (User Story 2.3 - Tool Execution)."""
        request = {
            "method": "tools/call",
            "params": {
                "name": "execute_query",
                "arguments": {
                    "query": "INSERT INTO users (name, email) VALUES ('Test User', 'test@example.com')"
                }
            }
        }
        
        response = await server.handle_request(request)
        
        assert "result" in response
        assert "1 rows affected" in response["result"]["content"][0]["text"]

    @pytest.mark.asyncio
    async def test_execute_query_update_success(self, server):
        """Test successful UPDATE query execution (User Story 2.3 - Tool Execution)."""
        request = {
            "method": "tools/call",
            "params": {
                "name": "execute_query",
                "arguments": {
                    "query": "UPDATE users SET name = 'Updated Name' WHERE id = 1"
                }
            }
        }
        
        response = await server.handle_request(request)
        
        assert "result" in response
        assert "rows affected" in response["result"]["content"][0]["text"]

    @pytest.mark.asyncio
    async def test_execute_query_delete_success(self, server):
        """Test successful DELETE query execution (User Story 2.3 - Tool Execution)."""
        request = {
            "method": "tools/call",
            "params": {
                "name": "execute_query",
                "arguments": {
                    "query": "DELETE FROM users WHERE id = 1"
                }
            }
        }
        
        response = await server.handle_request(request)
        
        assert "result" in response
        assert "rows affected" in response["result"]["content"][0]["text"]

    @pytest.mark.asyncio
    async def test_execute_query_invalid_syntax(self, server):
        """Test invalid SQL syntax (Negative scenario)."""
        request = {
            "method": "tools/call",
            "params": {
                "name": "execute_query",
                "arguments": {
                    "query": "INVALID SQL SYNTAX"
                }
            }
        }
        
        response = await server.handle_request(request)
        
        assert "error" in response
        assert response["error"]["code"] == -32603
        assert "Database error" in response["error"]["message"]

    @pytest.mark.asyncio
    async def test_execute_query_empty_query(self, server):
        """Test empty query (Negative scenario)."""
        request = {
            "method": "tools/call",
            "params": {
                "name": "execute_query",
                "arguments": {
                    "query": ""
                }
            }
        }
        
        response = await server.handle_request(request)
        
        assert "error" in response
        assert response["error"]["code"] == -32602
        assert "Query cannot be empty" in response["error"]["message"]

    @pytest.mark.asyncio
    async def test_insert_data_success(self, server):
        """Test successful data insertion (User Story 2.3 - Tool Execution)."""
        request = {
            "method": "tools/call",
            "params": {
                "name": "insert_data",
                "arguments": {
                    "table": "users",
                    "data": {
                        "name": "New User",
                        "email": "newuser@example.com"
                    }
                }
            }
        }
        
        response = await server.handle_request(request)
        
        assert "result" in response
        assert "Data inserted successfully" in response["result"]["content"][0]["text"]

    @pytest.mark.asyncio
    async def test_insert_data_missing_table(self, server):
        """Test data insertion with missing table name (Negative scenario)."""
        request = {
            "method": "tools/call",
            "params": {
                "name": "insert_data",
                "arguments": {
                    "data": {
                        "name": "Test User"
                    }
                }
            }
        }
        
        response = await server.handle_request(request)
        
        assert "error" in response
        assert response["error"]["code"] == -32602
        assert "Table name and data are required" in response["error"]["message"]

    @pytest.mark.asyncio
    async def test_insert_data_missing_data(self, server):
        """Test data insertion with missing data (Negative scenario)."""
        request = {
            "method": "tools/call",
            "params": {
                "name": "insert_data",
                "arguments": {
                    "table": "users"
                }
            }
        }
        
        response = await server.handle_request(request)
        
        assert "error" in response
        assert response["error"]["code"] == -32602
        assert "Table name and data are required" in response["error"]["message"]

    @pytest.mark.asyncio
    async def test_insert_data_invalid_table(self, server):
        """Test data insertion into non-existent table (Negative scenario)."""
        request = {
            "method": "tools/call",
            "params": {
                "name": "insert_data",
                "arguments": {
                    "table": "nonexistent_table",
                    "data": {
                        "name": "Test User"
                    }
                }
            }
        }
        
        response = await server.handle_request(request)
        
        assert "error" in response
        assert response["error"]["code"] == -32603
        assert "Database error" in response["error"]["message"]

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
        assert len(response["result"]["resources"]) == 2
        
        resource_uris = [resource["uri"] for resource in response["result"]["resources"]]
        assert "db://tables/users" in resource_uris
        assert "db://tables/products" in resource_uris

    @pytest.mark.asyncio
    async def test_resource_read_table_success(self, server):
        """Test successful table resource reading (User Story 2.3 - Tool Execution)."""
        request = {
            "method": "resources/read",
            "params": {
                "uri": "db://tables/users"
            }
        }
        
        response = await server.handle_request(request)
        
        assert "result" in response
        assert "content" in response["result"]
        
        results = json.loads(response["result"]["content"][0]["text"])
        assert len(results) > 0
        assert "name" in results[0]
        assert "email" in results[0]

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
                "name": "describe_table",
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
    async def test_complex_query_operations(self, server):
        """Test complex query operations (Complex scenario)."""
        # Insert test data
        insert_request = {
            "method": "tools/call",
            "params": {
                "name": "execute_query",
                "arguments": {
                    "query": "INSERT INTO users (name, email) VALUES ('Complex User', 'complex@example.com')"
                }
            }
        }
        
        insert_response = await server.handle_request(insert_request)
        assert "result" in insert_response
        
        # Query with JOIN
        join_request = {
            "method": "tools/call",
            "params": {
                "name": "execute_query",
                "arguments": {
                    "query": "SELECT u.name, p.name as product_name FROM users u, products p LIMIT 1"
                }
            }
        }
        
        join_response = await server.handle_request(join_request)
        assert "result" in join_response
        
        results = json.loads(join_response["result"]["content"][0]["text"])
        assert len(results) == 1
        assert "name" in results[0]
        assert "product_name" in results[0]

    @pytest.mark.asyncio
    async def test_transaction_rollback_simulation(self, server):
        """Test transaction rollback simulation (Complex scenario)."""
        # Count initial users
        count_request = {
            "method": "tools/call",
            "params": {
                "name": "execute_query",
                "arguments": {
                    "query": "SELECT COUNT(*) as count FROM users"
                }
            }
        }
        
        count_response = await server.handle_request(count_request)
        initial_count = json.loads(count_response["result"]["content"][0]["text"])[0]["count"]
        
        # Insert a user
        insert_request = {
            "method": "tools/call",
            "params": {
                "name": "execute_query",
                "arguments": {
                    "query": "INSERT INTO users (name, email) VALUES ('Rollback User', 'rollback@example.com')"
                }
            }
        }
        
        insert_response = await server.handle_request(insert_request)
        assert "result" in insert_response
        
        # Verify user was inserted
        count_response = await server.handle_request(count_request)
        new_count = json.loads(count_response["result"]["content"][0]["text"])[0]["count"]
        assert new_count == initial_count + 1

    @pytest.mark.asyncio
    async def test_concurrent_operations(self, server):
        """Test concurrent database operations (Concurrency scenario)."""
        async def insert_user(name, email):
            request = {
                "method": "tools/call",
                "params": {
                    "name": "execute_query",
                    "arguments": {
                        "query": f"INSERT INTO users (name, email) VALUES ('{name}', '{email}')"
                    }
                }
            }
            return await server.handle_request(request)
        
        # Run multiple insert operations concurrently
        tasks = [
            insert_user(f"Concurrent User {i}", f"user{i}@example.com")
            for i in range(3)
        ]
        
        responses = await asyncio.gather(*tasks)
        
        # All should succeed
        for response in responses:
            assert "result" in response
        
        # Verify all users were inserted
        count_request = {
            "method": "tools/call",
            "params": {
                "name": "execute_query",
                "arguments": {
                    "query": "SELECT COUNT(*) as count FROM users WHERE name LIKE 'Concurrent User%'"
                }
            }
        }
        
        count_response = await server.handle_request(count_request)
        count = json.loads(count_response["result"]["content"][0]["text"])[0]["count"]
        assert count == 3

    @pytest.mark.asyncio
    async def test_data_validation_scenarios(self, server):
        """Test data validation scenarios (Complex scenario)."""
        # Test inserting data with all fields
        full_data_request = {
            "method": "tools/call",
            "params": {
                "name": "insert_data",
                "arguments": {
                    "table": "users",
                    "data": {
                        "name": "Full User",
                        "email": "full@example.com"
                    }
                }
            }
        }
        
        response = await server.handle_request(full_data_request)
        assert "result" in response
        
        # Test inserting product data
        product_request = {
            "method": "tools/call",
            "params": {
                "name": "insert_data",
                "arguments": {
                    "table": "products",
                    "data": {
                        "name": "Test Product",
                        "price": 99.99,
                        "category": "Test Category"
                    }
                }
            }
        }
        
        response = await server.handle_request(product_request)
        assert "result" in response
        
        # Verify both records exist
        verify_request = {
            "method": "tools/call",
            "params": {
                "name": "execute_query",
                "arguments": {
                    "query": "SELECT name FROM users WHERE name = 'Full User' UNION SELECT name FROM products WHERE name = 'Test Product'"
                }
            }
        }
        
        verify_response = await server.handle_request(verify_request)
        results = json.loads(verify_response["result"]["content"][0]["text"])
        assert len(results) == 2

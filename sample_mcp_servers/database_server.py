#!/usr/bin/env python3
"""
Sample MCP Database Server
Implements database operations for testing SprintConnect
"""

import asyncio
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add the current directory to Python path for imports
sys.path.insert(0, sys.path[0])

class DatabaseMCPServer:
    """Sample MCP server implementing database operations."""
    
    def __init__(self, db_path: str = "/tmp/mcp_test.db"):
        self.db_path = Path(db_path)
        self.server_info = {
            "name": "database-server",
            "version": "1.0.0",
            "description": "Sample database MCP server for testing",
            "capabilities": {
                "tools": ["execute_query", "list_tables", "describe_table", "insert_data"],
                "resources": ["db://tables/*", "db://schemas/*"]
            }
        }
        self._init_database()
    
    def _init_database(self):
        """Initialize the test database with sample data."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create sample tables
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                price DECIMAL(10,2) NOT NULL,
                category TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Insert sample data
        cursor.execute("DELETE FROM users")  # Clear existing data
        cursor.execute("DELETE FROM products")  # Clear existing data
        
        users_data = [
            ("John Doe", "john@example.com"),
            ("Jane Smith", "jane@example.com"),
            ("Bob Johnson", "bob@example.com")
        ]
        
        products_data = [
            ("Laptop", 999.99, "Electronics"),
            ("Book", 19.99, "Education"),
            ("Coffee", 4.99, "Food")
        ]
        
        cursor.executemany("INSERT INTO users (name, email) VALUES (?, ?)", users_data)
        cursor.executemany("INSERT INTO products (name, price, category) VALUES (?, ?, ?)", products_data)
        
        conn.commit()
        conn.close()
    
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
                        "name": "execute_query",
                        "description": "Execute a SQL query",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "query": {
                                    "type": "string",
                                    "description": "SQL query to execute"
                                }
                            },
                            "required": ["query"]
                        }
                    },
                    {
                        "name": "list_tables",
                        "description": "List all tables in the database",
                        "inputSchema": {
                            "type": "object",
                            "properties": {}
                        }
                    },
                    {
                        "name": "describe_table",
                        "description": "Get schema information for a table",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "table_name": {
                                    "type": "string",
                                    "description": "Name of the table to describe"
                                }
                            },
                            "required": ["table_name"]
                        }
                    },
                    {
                        "name": "insert_data",
                        "description": "Insert data into a table",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "table": {
                                    "type": "string",
                                    "description": "Table name"
                                },
                                "data": {
                                    "type": "object",
                                    "description": "Data to insert"
                                }
                            },
                            "required": ["table", "data"]
                        }
                    }
                ]
            }
        }
    
    async def _handle_tool_call(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tool execution."""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        if tool_name == "execute_query":
            return await self._execute_query(arguments)
        elif tool_name == "list_tables":
            return await self._list_tables()
        elif tool_name == "describe_table":
            return await self._describe_table(arguments)
        elif tool_name == "insert_data":
            return await self._insert_data(arguments)
        else:
            return {
                "error": {
                    "code": -32601,
                    "message": f"Tool not found: {tool_name}"
                }
            }
    
    async def _execute_query(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a SQL query."""
        query = args.get("query", "")
        
        if not query.strip():
            return {
                "error": {
                    "code": -32602,
                    "message": "Query cannot be empty"
                }
            }
        
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Enable column access by name
            cursor = conn.cursor()
            
            cursor.execute(query)
            
            if query.strip().upper().startswith(("SELECT", "PRAGMA", "EXPLAIN")):
                # For SELECT queries, return results
                rows = cursor.fetchall()
                results = [dict(row) for row in rows]
                
                conn.close()
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
            else:
                # For INSERT/UPDATE/DELETE queries
                conn.commit()
                affected_rows = cursor.rowcount
                conn.close()
                
                return {
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": f"Query executed successfully. {affected_rows} rows affected."
                            }
                        ]
                    }
                }
                
        except sqlite3.Error as e:
            return {
                "error": {
                    "code": -32603,
                    "message": f"Database error: {str(e)}"
                }
            }
        except Exception as e:
            return {
                "error": {
                    "code": -32603,
                    "message": f"Error executing query: {str(e)}"
                }
            }
    
    async def _list_tables(self) -> Dict[str, Any]:
        """List all tables in the database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            conn.close()
            
            return {
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(tables, indent=2)
                        }
                    ]
                }
            }
        except Exception as e:
            return {
                "error": {
                    "code": -32603,
                    "message": f"Error listing tables: {str(e)}"
                }
            }
    
    async def _describe_table(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get schema information for a table."""
        table_name = args.get("table_name", "")
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            if not columns:
                conn.close()
                return {
                    "error": {
                        "code": -32602,
                        "message": f"Table not found: {table_name}"
                    }
                }
            
            schema = []
            for col in columns:
                schema.append({
                    "name": col[1],
                    "type": col[2],
                    "not_null": bool(col[3]),
                    "default_value": col[4],
                    "primary_key": bool(col[5])
                })
            
            conn.close()
            
            return {
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(schema, indent=2)
                        }
                    ]
                }
            }
        except Exception as e:
            return {
                "error": {
                    "code": -32603,
                    "message": f"Error describing table: {str(e)}"
                }
            }
    
    async def _insert_data(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Insert data into a table."""
        table = args.get("table", "")
        data = args.get("data", {})
        
        if not table or not data:
            return {
                "error": {
                    "code": -32602,
                    "message": "Table name and data are required"
                }
            }
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            columns = list(data.keys())
            values = list(data.values())
            placeholders = ", ".join(["?" for _ in columns])
            
            query = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})"
            cursor.execute(query, values)
            
            conn.commit()
            conn.close()
            
            return {
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Data inserted successfully into {table}"
                        }
                    ]
                }
            }
        except sqlite3.Error as e:
            return {
                "error": {
                    "code": -32603,
                    "message": f"Database error: {str(e)}"
                }
            }
        except Exception as e:
            return {
                "error": {
                    "code": -32603,
                    "message": f"Error inserting data: {str(e)}"
                }
            }
    
    async def _handle_resources_list(self) -> Dict[str, Any]:
        """List available resources."""
        return {
            "result": {
                "resources": [
                    {
                        "uri": "db://tables/users",
                        "name": "Users Table",
                        "description": "User data table",
                        "mimeType": "application/json"
                    },
                    {
                        "uri": "db://tables/products",
                        "name": "Products Table",
                        "description": "Product data table",
                        "mimeType": "application/json"
                    }
                ]
            }
        }
    
    async def _handle_resource_read(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Read a resource."""
        uri = params.get("uri", "")
        
        if uri.startswith("db://tables/"):
            table_name = uri[12:]  # Remove "db://tables/" prefix
            return await self._execute_query({"query": f"SELECT * FROM {table_name}"})
        else:
            return {
                "error": {
                    "code": -32602,
                    "message": f"Unsupported resource URI: {uri}"
                }
            }

async def main():
    """Main server loop."""
    server = DatabaseMCPServer()
    
    print("Database MCP Server starting...")
    print(f"Database path: {server.db_path}")
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

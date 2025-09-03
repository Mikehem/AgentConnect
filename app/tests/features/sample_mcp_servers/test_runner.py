#!/usr/bin/env python3
"""
Test runner for sample MCP servers.
Runs all tests for the sample MCP servers and integration tests.
"""

import subprocess
import sys
import os
from pathlib import Path

def run_tests():
    """Run all sample MCP server tests."""
    print("🚀 Running Sample MCP Server Tests")
    print("=" * 50)
    
    # Get the test directory
    test_dir = Path(__file__).parent
    
    # List of test files to run
    test_files = [
        "test_filesystem_server.py",
        "test_github_server.py", 
        "test_database_server.py",
        "test_sprintconnect_integration.py"
    ]
    
    total_tests = 0
    passed_tests = 0
    failed_tests = 0
    
    for test_file in test_files:
        test_path = test_dir / test_file
        if not test_path.exists():
            print(f"❌ Test file not found: {test_file}")
            continue
            
        print(f"\n📋 Running {test_file}...")
        print("-" * 30)
        
        try:
            # Run the test file
            result = subprocess.run([
                sys.executable, "-m", "pytest", 
                str(test_path), 
                "-v", 
                "--tb=short"
            ], capture_output=True, text=True, cwd=os.getcwd())
            
            if result.returncode == 0:
                print(f"✅ {test_file} - PASSED")
                # Count tests from output
                lines = result.stdout.split('\n')
                for line in lines:
                    if 'PASSED' in line:
                        passed_tests += 1
                        total_tests += 1
            else:
                print(f"❌ {test_file} - FAILED")
                print("STDOUT:", result.stdout)
                print("STDERR:", result.stderr)
                # Count failed tests
                lines = result.stdout.split('\n')
                for line in lines:
                    if 'FAILED' in line:
                        failed_tests += 1
                        total_tests += 1
                        
        except Exception as e:
            print(f"❌ Error running {test_file}: {e}")
            failed_tests += 1
            total_tests += 1
    
    print("\n" + "=" * 50)
    print("📊 Test Summary")
    print("=" * 50)
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {failed_tests}")
    
    if failed_tests == 0:
        print("🎉 All tests passed!")
        return 0
    else:
        print("💥 Some tests failed!")
        return 1

def run_sample_servers_demo():
    """Run a quick demo of the sample MCP servers."""
    print("\n🎭 Sample MCP Servers Demo")
    print("=" * 50)
    
    # Test filesystem server
    print("\n📁 Testing Filesystem Server...")
    try:
        from filesystem_server import FilesystemMCPServer
        import asyncio
        import tempfile
        
        async def test_filesystem():
            with tempfile.TemporaryDirectory() as temp_dir:
                server = FilesystemMCPServer(base_path=temp_dir)
                
                # Test initialization
                init_request = {
                    "method": "initialize",
                    "params": {"protocolVersion": "2024-11-05"}
                }
                response = await server.handle_request(init_request)
                print(f"✅ Initialization: {response['result']['serverInfo']['name']}")
                
                # Test write file
                write_request = {
                    "method": "tools/call",
                    "params": {
                        "name": "write_file",
                        "arguments": {
                            "path": "demo.txt",
                            "content": "Hello from SprintConnect!"
                        }
                    }
                }
                response = await server.handle_request(write_request)
                print(f"✅ Write file: {response['result']['content'][0]['text']}")
                
                # Test read file
                read_request = {
                    "method": "tools/call",
                    "params": {
                        "name": "read_file",
                        "arguments": {"path": "demo.txt"}
                    }
                }
                response = await server.handle_request(read_request)
                print(f"✅ Read file: {response['result']['content'][0]['text']}")
        
        asyncio.run(test_filesystem())
        
    except Exception as e:
        print(f"❌ Filesystem server demo failed: {e}")
    
    # Test GitHub server
    print("\n🐙 Testing GitHub Server...")
    try:
        from github_server import GitHubMCPServer
        import asyncio
        
        async def test_github():
            server = GitHubMCPServer()
            
            # Test initialization
            init_request = {
                "method": "initialize",
                "params": {"protocolVersion": "2024-11-05"}
            }
            response = await server.handle_request(init_request)
            print(f"✅ Initialization: {response['result']['serverInfo']['name']}")
            
            # Test get repo info
            repo_request = {
                "method": "tools/call",
                "params": {
                    "name": "get_repo_info",
                    "arguments": {
                        "owner": "testuser",
                        "repo": "testrepo"
                    }
                }
            }
            response = await server.handle_request(repo_request)
            import json
            repo_info = json.loads(response['result']['content'][0]['text'])
            print(f"✅ Repository info: {repo_info['name']} ({repo_info['language']})")
        
        asyncio.run(test_github())
        
    except Exception as e:
        print(f"❌ GitHub server demo failed: {e}")
    
    # Test database server
    print("\n🗄️ Testing Database Server...")
    try:
        from database_server import DatabaseMCPServer
        import asyncio
        import tempfile
        
        async def test_database():
            with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_file:
                temp_path = temp_file.name
            
            try:
                server = DatabaseMCPServer(db_path=temp_path)
                
                # Test initialization
                init_request = {
                    "method": "initialize",
                    "params": {"protocolVersion": "2024-11-05"}
                }
                response = await server.handle_request(init_request)
                print(f"✅ Initialization: {response['result']['serverInfo']['name']}")
                
                # Test list tables
                tables_request = {
                    "method": "tools/call",
                    "params": {
                        "name": "list_tables",
                        "arguments": {}
                    }
                }
                response = await server.handle_request(tables_request)
                import json
                tables = json.loads(response['result']['content'][0]['text'])
                print(f"✅ Tables: {', '.join(tables)}")
                
                # Test query
                query_request = {
                    "method": "tools/call",
                    "params": {
                        "name": "execute_query",
                        "arguments": {
                            "query": "SELECT COUNT(*) as count FROM users"
                        }
                    }
                }
                response = await server.handle_request(query_request)
                result = json.loads(response['result']['content'][0]['text'])
                print(f"✅ User count: {result[0]['count']}")
                
            finally:
                # Clean up
                os.unlink(temp_path)
        
        asyncio.run(test_database())
        
    except Exception as e:
        print(f"❌ Database server demo failed: {e}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run sample MCP server tests")
    parser.add_argument("--demo", action="store_true", help="Run demo instead of tests")
    
    args = parser.parse_args()
    
    if args.demo:
        run_sample_servers_demo()
    else:
        exit_code = run_tests()
        sys.exit(exit_code)

#!/usr/bin/env python3
"""Comprehensive test runner for SprintConnect backend."""

import sys
import subprocess
import argparse
from pathlib import Path


def run_command(cmd, description):
    """Run a command and handle errors."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'='*60}")
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.stdout:
        print("STDOUT:")
        print(result.stdout)
    
    if result.stderr:
        print("STDERR:")
        print(result.stderr)
    
    if result.returncode != 0:
        print(f"❌ {description} failed with exit code {result.returncode}")
        return False
    else:
        print(f"✅ {description} completed successfully")
        return True


def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(description="SprintConnect Backend Test Runner")
    parser.add_argument(
        "--test-type",
        choices=["all", "unit", "integration", "api", "service", "schema", "security", "auth", "health", "capabilities", "mcp_protocol", "mcp_registration", "smoke"],
        default="all",
        help="Type of tests to run"
    )
    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Generate coverage report"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Verbose output"
    )
    parser.add_argument(
        "--fast",
        action="store_true",
        help="Skip slow tests"
    )
    
    args = parser.parse_args()
    
    # Base pytest command
    base_cmd = ["poetry", "run", "pytest"]
    
    if args.verbose:
        base_cmd.append("-v")
    
    if args.coverage:
        base_cmd.extend(["--cov=app", "--cov-report=term-missing", "--cov-report=html"])
    
    if args.fast:
        base_cmd.append("-m not slow")
    
    # Test type specific commands
    if args.test_type == "all":
        test_commands = [
            (base_cmd + ["app/tests/features/mcp_servers/"], "MCP Servers Feature Tests"),
            (base_cmd + ["app/tests/features/auth/"], "Authentication Feature Tests"),
            (base_cmd + ["app/tests/features/organizations/"], "Organizations Feature Tests"),
            (base_cmd + ["app/tests/features/capabilities/"], "Capabilities Feature Tests"),
            (base_cmd + ["app/tests/features/health/"], "Health Monitoring Feature Tests"),
        ]
    elif args.test_type == "unit":
        test_commands = [
            (base_cmd + ["-m unit"], "Unit Tests"),
        ]
    elif args.test_type == "integration":
        test_commands = [
            (base_cmd + ["-m integration"], "Integration Tests"),
        ]
    elif args.test_type == "api":
        test_commands = [
            (base_cmd + ["-m api"], "API Tests"),
        ]
    elif args.test_type == "service":
        test_commands = [
            (base_cmd + ["-m service"], "Service Tests"),
        ]
    elif args.test_type == "schema":
        test_commands = [
            (base_cmd + ["-m schema"], "Schema Tests"),
        ]
    elif args.test_type == "security":
        test_commands = [
            (base_cmd + ["-m security"], "Security Tests"),
        ]
    elif args.test_type == "auth":
        test_commands = [
            (base_cmd + ["app/tests/features/auth/"], "Authentication Tests"),
        ]
    elif args.test_type == "health":
        test_commands = [
            (base_cmd + ["app/tests/features/health/"], "Health Monitoring Tests"),
        ]
    elif args.test_type == "capabilities":
        test_commands = [
            (base_cmd + ["app/tests/features/capabilities/"], "Capabilities Tests"),
        ]
    elif args.test_type == "mcp_protocol":
        test_commands = [
            (base_cmd + ["app/tests/features/mcp_servers/test_mcp_protocol.py"], "MCP Protocol Tests"),
        ]
    elif args.test_type == "mcp_registration":
        test_commands = [
            (base_cmd + ["app/tests/features/mcp_servers/test_mcp_registration_service.py"], "MCP Registration Service Tests"),
        ]
    elif args.test_type == "smoke":
        test_commands = [
            (base_cmd + ["-m smoke"], "Smoke Tests"),
        ]
    
    # Run tests
    success = True
    for cmd, description in test_commands:
        if not run_command(cmd, description):
            success = False
    
    # Summary
    print(f"\n{'='*60}")
    if success:
        print("🎉 All tests completed successfully!")
        sys.exit(0)
    else:
        print("❌ Some tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()

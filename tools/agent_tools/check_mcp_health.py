#!/usr/bin/env python3
"""Check health of all MCP servers.

Provides a health check for MCP servers configured in the project.
Returns JSON output with server status and issues.

Usage:
    uv run python -m tools.agent_tools.check_mcp_health
    uv run python -m tools.agent_tools.check_mcp_health --verbose
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


# Server configuration
MCP_SERVERS: Dict[str, Dict[str, Any]] = {
    "slurm-agent-tools": {
        "module": "tools.mcp_servers.slurm_agent_tools",
        "expected_tools": 7,
        "description": "SLURM job management tools",
        "test_import": "tools.mcp_servers.slurm_agent_tools",
    },
    "slurm-tracker": {
        "module": "tools.mcp_servers.slurm_server",
        "expected_tools": 9,
        "description": "SLURM job tracking and monitoring",
        "test_import": "tools.mcp_servers.slurm_server",
    },
    "memory": {
        "module": "mcp_memory_service",
        "expected_tools": 24,
        "description": "Memory storage and retrieval",
        "test_import": None,  # External package
    },
}


def check_module_import(module_name: str) -> Dict[str, Any]:
    """Check if a Python module can be imported.
    
    Args:
        module_name: Fully qualified module name
    
    Returns:
        Status dict with "importable" bool and optional "error" message
    """
    try:
        __import__(module_name)
        return {"importable": True}
    except ImportError as e:
        return {"importable": False, "error": str(e)}
    except Exception as e:
        return {"importable": False, "error": f"Unexpected error: {e}"}


def check_server_process(module: str) -> Dict[str, Any]:
    """Check if a server process can start.
    
    Args:
        module: Module to run with python -m
    
    Returns:
        Status dict with process check results
    """
    try:
        # Try to start the server briefly
        proc = subprocess.Popen(
            ["uv", "run", "python", "-m", module],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        
        # Wait briefly
        import time
        time.sleep(0.5)
        
        # Check if still running or exited cleanly
        exit_code = proc.poll()
        
        # Terminate the process
        proc.terminate()
        try:
            proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
        
        if exit_code is None:
            # Process was still running = good
            return {"startable": True, "status": "running"}
        elif exit_code == 0:
            # Exited cleanly (maybe no client)
            return {"startable": True, "status": "exited_cleanly"}
        else:
            return {"startable": False, "status": "crashed", "exit_code": exit_code}
            
    except FileNotFoundError:
        return {"startable": False, "error": "uv command not found"}
    except Exception as e:
        return {"startable": False, "error": str(e)}


def check_mcp_health(verbose: bool = False) -> Dict[str, Any]:
    """Check health of all MCP servers.
    
    Args:
        verbose: Include detailed diagnostics
    
    Returns:
        Health status dict with:
            - status: "healthy" | "degraded" | "unavailable"
            - servers: Per-server status
            - issues: List of detected issues
    """
    results: Dict[str, Dict[str, Any]] = {}
    issues: List[str] = []
    
    for server_name, config in MCP_SERVERS.items():
        server_status: Dict[str, Any] = {
            "description": config["description"],
            "expected_tools": config["expected_tools"],
        }
        
        # Check module import
        test_import = config.get("test_import")
        if test_import:
            import_result = check_module_import(test_import)
            server_status["module_importable"] = import_result["importable"]
            
            if not import_result["importable"]:
                server_status["status"] = "unavailable"
                issues.append(f"{server_name}: Module import failed - {import_result.get('error', 'unknown')}")
            else:
                server_status["status"] = "available"
        else:
            # External package - assume available if not testing
            server_status["status"] = "external"
            server_status["module_importable"] = None
        
        # Verbose: check if process can start
        if verbose and test_import and server_status.get("module_importable"):
            process_result = check_server_process(config["module"])
            server_status["process_check"] = process_result
            
            if not process_result.get("startable"):
                server_status["status"] = "error"
                issues.append(f"{server_name}: Process start failed - {process_result.get('error', 'unknown')}")
        
        results[server_name] = server_status
    
    # Determine overall status
    available_count = sum(1 for s in results.values() if s["status"] in ["available", "external"])
    total_count = len(results)
    
    if available_count == total_count:
        overall_status = "healthy"
    elif available_count > 0:
        overall_status = "degraded"
    else:
        overall_status = "unavailable"
    
    return {
        "status": overall_status,
        "timestamp": datetime.now().isoformat(),
        "servers": results,
        "issues": issues,
        "summary": {
            "total_servers": total_count,
            "available_servers": available_count,
            "issues_count": len(issues),
        },
    }


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Check health of all MCP servers (JSON output)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Basic health check
    uv run python -m tools.agent_tools.check_mcp_health
    
    # Verbose check with process testing
    uv run python -m tools.agent_tools.check_mcp_health --verbose
    
Exit codes:
    0 - All servers healthy
    1 - Some servers degraded
    2 - All servers unavailable
        """,
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Include detailed diagnostics (slower)",
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Only output JSON, no extra messages",
    )
    
    args = parser.parse_args()
    
    # Run health check
    result = check_mcp_health(verbose=args.verbose)
    
    # Output JSON
    print(json.dumps(result, indent=2))
    
    # Exit code based on status
    if result["status"] == "healthy":
        sys.exit(0)
    elif result["status"] == "degraded":
        sys.exit(1)
    else:
        sys.exit(2)


if __name__ == "__main__":
    main()

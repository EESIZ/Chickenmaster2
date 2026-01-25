#!/usr/bin/env python3
"""MCP Server for SLURM Agent Tools.

Exposes the agent tools from tools/agent_tools/ as MCP functions,
enabling AI agents to interact with SLURM jobs, experiment results,
and project status through the Model Context Protocol.

Usage:
    uv run python -m tools.mcp_servers.slurm_agent_tools

MCP Tools:
    - slurm_agent_submit_job: Submit SLURM job script
    - slurm_agent_wait_for_job: Wait for job completion
    - slurm_agent_analyze_log: Analyze job logs
    - slurm_agent_get_status: Get project/cluster status
    - slurm_agent_save_result: Save experiment results
    - slurm_agent_compare_results: Compare experiment results
    - slurm_agent_validate_config: Validate configuration file
"""

from __future__ import annotations

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# MCP SDK imports
try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import (
        TextContent,
        Tool,
    )
except ImportError:
    print(
        "Error: MCP SDK not installed. Run: uv add mcp",
        file=sys.stderr,
    )
    sys.exit(1)


def get_project_root() -> Path:
    """Return project root directory."""
    return Path(__file__).parent.parent.parent


# Import agent tool functions
# We import the core functions, not the CLI entry points
sys.path.insert(0, str(get_project_root()))

from tools.agent_tools.submit_job import (
    check_safety_limits,
    load_agent_policy,
    submit_slurm_job,
)
from tools.agent_tools.wait_for_job import (
    get_job_status,
    wait_for_job,
)
from tools.agent_tools.analyze_log import (
    analyze_log_file,
    find_log_by_job_id,
)
from tools.agent_tools.get_status import (
    get_project_status,
)
from tools.agent_tools.save_result import (
    save_experiment_result,
)
from tools.agent_tools.compare_results import (
    compare_results as compare_results_impl,
)
from tools.agent_tools.validate_config import (
    validate_config as validate_config_impl,
)


# Initialize MCP server
server = Server("slurm-agent-tools")


def create_error_response(
    error_type: str,
    message: str,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create standardized error response.
    
    Args:
        error_type: Type of error (e.g., ValidationError, FileNotFoundError)
        message: Human-readable error message
        details: Optional additional error details
        
    Returns:
        Error response dictionary
    """
    response: dict[str, Any] = {
        "status": "error",
        "error_type": error_type,
        "message": message,
        "timestamp": datetime.now().isoformat(),
    }
    if details:
        response["details"] = details
    return response


def validate_json_output(result: Any) -> dict[str, Any]:
    """Validate and ensure output is JSON-serializable.
    
    Args:
        result: Result to validate
        
    Returns:
        Validated result or error response
    """
    try:
        # Test JSON serialization
        json.dumps(result)
        return result if isinstance(result, dict) else {"result": result}
    except (TypeError, ValueError) as e:
        return create_error_response(
            "SerializationError",
            f"Failed to serialize result to JSON: {e}",
        )


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available SLURM agent tools."""
    return [
        Tool(
            name="slurm_agent_submit_job",
            description="Submit a SLURM job script. Performs safety checks including "
                        "max concurrent jobs limit before submission.",
            inputSchema={
                "type": "object",
                "properties": {
                    "script": {
                        "type": "string",
                        "description": "Path to SLURM script (relative to scripts/slurm/)",
                    },
                    "job_name": {
                        "type": "string",
                        "description": "Optional job name for SLURM",
                    },
                    "args": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional additional arguments to pass to script",
                    },
                    "skip_safety_check": {
                        "type": "boolean",
                        "description": "Skip safety checks (not recommended)",
                        "default": False,
                    },
                    "dry_run": {
                        "type": "boolean",
                        "description": "Return command without executing",
                        "default": False,
                    },
                },
                "required": ["script"],
            },
        ),
        Tool(
            name="slurm_agent_wait_for_job",
            description="Wait for a SLURM job to complete. Polls job status until "
                        "completion, failure, or timeout.",
            inputSchema={
                "type": "object",
                "properties": {
                    "job_id": {
                        "type": "string",
                        "description": "SLURM job ID to wait for",
                    },
                    "timeout_seconds": {
                        "type": "integer",
                        "description": "Maximum wait time in seconds (default: 28800 = 8 hours)",
                        "default": 28800,
                    },
                    "poll_interval": {
                        "type": "integer",
                        "description": "Polling interval in seconds (default: 30)",
                        "default": 30,
                    },
                    "no_wait": {
                        "type": "boolean",
                        "description": "Check status once without waiting",
                        "default": False,
                    },
                },
                "required": ["job_id"],
            },
        ),
        Tool(
            name="slurm_agent_analyze_log",
            description="Analyze SLURM job log files for errors, warnings, and metrics. "
                        "Can find logs by job ID or analyze a specific file.",
            inputSchema={
                "type": "object",
                "properties": {
                    "job_id": {
                        "type": "string",
                        "description": "SLURM job ID to find and analyze logs for",
                    },
                    "path": {
                        "type": "string",
                        "description": "Direct path to log file to analyze",
                    },
                    "mode": {
                        "type": "string",
                        "enum": ["auto", "error", "metrics", "full"],
                        "description": "Analysis mode (default: auto)",
                        "default": "auto",
                    },
                    "recent_errors": {
                        "type": "boolean",
                        "description": "Analyze all recent error logs",
                        "default": False,
                    },
                },
                "required": [],
            },
        ),
        Tool(
            name="slurm_agent_get_status",
            description="Get comprehensive project and cluster status including "
                        "SLURM jobs, GPU availability, recent results, and error logs.",
            inputSchema={
                "type": "object",
                "properties": {
                    "detailed": {
                        "type": "boolean",
                        "description": "Include detailed information (tasks, disk usage)",
                        "default": False,
                    },
                    "section": {
                        "type": "string",
                        "enum": ["jobs", "gpu", "results", "errors", "tasks", "disk"],
                        "description": "Query specific section only",
                    },
                    "no_cache": {
                        "type": "boolean",
                        "description": "Bypass cache and fetch fresh data",
                        "default": False,
                    },
                },
                "required": [],
            },
        ),
        Tool(
            name="slurm_agent_save_result",
            description="Save experiment results with standardized schema and validation. "
                        "Automatically adds metadata including git info and environment.",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Experiment name",
                    },
                    "status": {
                        "type": "string",
                        "enum": ["success", "failed", "cancelled"],
                        "description": "Experiment status (default: success)",
                        "default": "success",
                    },
                    "config": {
                        "type": "object",
                        "description": "Experiment configuration dictionary",
                    },
                    "metrics": {
                        "type": "object",
                        "description": "Experiment metrics dictionary",
                    },
                    "baseline": {
                        "type": "string",
                        "description": "Baseline experiment file path for diff computation",
                    },
                    "notes": {
                        "type": "string",
                        "description": "Experiment notes",
                    },
                    "output_dir": {
                        "type": "string",
                        "description": "Output directory (default: results)",
                        "default": "results",
                    },
                    "dry_run": {
                        "type": "boolean",
                        "description": "Return result without saving",
                        "default": False,
                    },
                },
                "required": ["name"],
            },
        ),
        Tool(
            name="slurm_agent_compare_results",
            description="Compare two experiment results and generate detailed diff "
                        "including metrics changes and configuration differences.",
            inputSchema={
                "type": "object",
                "properties": {
                    "baseline": {
                        "type": "string",
                        "description": "Path to baseline experiment result JSON",
                    },
                    "target": {
                        "type": "string",
                        "description": "Path to target experiment result JSON",
                    },
                    "metrics_only": {
                        "type": "boolean",
                        "description": "Only compare metrics (skip config and environment)",
                        "default": False,
                    },
                },
                "required": ["baseline", "target"],
            },
        ),
        Tool(
            name="slurm_agent_validate_config",
            description="Validate experiment configuration file for required fields, "
                        "valid types, ranges, and path existence.",
            inputSchema={
                "type": "object",
                "properties": {
                    "config_path": {
                        "type": "string",
                        "description": "Path to configuration file (YAML or JSON)",
                    },
                    "strict": {
                        "type": "boolean",
                        "description": "Treat warnings as errors",
                        "default": False,
                    },
                },
                "required": ["config_path"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Handle tool calls for SLURM agent operations."""
    
    try:
        if name == "slurm_agent_submit_job":
            result = await handle_submit_job(arguments)
        elif name == "slurm_agent_wait_for_job":
            result = await handle_wait_for_job(arguments)
        elif name == "slurm_agent_analyze_log":
            result = await handle_analyze_log(arguments)
        elif name == "slurm_agent_get_status":
            result = await handle_get_status(arguments)
        elif name == "slurm_agent_save_result":
            result = await handle_save_result(arguments)
        elif name == "slurm_agent_compare_results":
            result = await handle_compare_results(arguments)
        elif name == "slurm_agent_validate_config":
            result = await handle_validate_config(arguments)
        else:
            result = create_error_response(
                "UnknownToolError",
                f"Unknown tool: {name}",
            )
        
        # Validate JSON output
        validated_result = validate_json_output(result)
        return [TextContent(type="text", text=json.dumps(validated_result, indent=2))]
        
    except Exception as e:
        error_result = create_error_response(
            "InternalError",
            f"Tool execution failed: {str(e)}",
            {"exception_type": type(e).__name__},
        )
        return [TextContent(type="text", text=json.dumps(error_result, indent=2))]


async def handle_submit_job(arguments: dict[str, Any]) -> dict[str, Any]:
    """Handle submit_job tool call.
    
    Args:
        arguments: Tool arguments containing script, job_name, etc.
        
    Returns:
        Job submission result
    """
    script = arguments.get("script")
    if not script:
        return create_error_response(
            "ValidationError",
            "Required parameter 'script' is missing",
        )
    
    job_name = arguments.get("job_name")
    args = arguments.get("args")
    skip_safety_check = arguments.get("skip_safety_check", False)
    dry_run = arguments.get("dry_run", False)
    
    # Safety check
    if not skip_safety_check:
        policy = load_agent_policy()
        safety_check = check_safety_limits(policy)
        
        if not safety_check.get("allowed", True):
            return {
                "status": "blocked",
                "reason": safety_check["reason"],
                "active_jobs": safety_check.get("active_jobs", []),
                "timestamp": datetime.now().isoformat(),
            }
    
    # Submit job (run in executor to avoid blocking)
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None,
        lambda: submit_slurm_job(
            script_path=script,
            job_name=job_name,
            args=args,
            dry_run=dry_run,
        ),
    )
    
    return result


async def handle_wait_for_job(arguments: dict[str, Any]) -> dict[str, Any]:
    """Handle wait_for_job tool call.
    
    Args:
        arguments: Tool arguments containing job_id, timeout, etc.
        
    Returns:
        Job completion status
    """
    job_id = arguments.get("job_id")
    if not job_id:
        return create_error_response(
            "ValidationError",
            "Required parameter 'job_id' is missing",
        )
    
    timeout_seconds = arguments.get("timeout_seconds", 28800)
    poll_interval = arguments.get("poll_interval", 30)
    no_wait = arguments.get("no_wait", False)
    
    if no_wait:
        # Just check status once
        loop = asyncio.get_event_loop()
        job_status = await loop.run_in_executor(None, lambda: get_job_status(job_id))
        
        if job_status:
            return {
                "status": "checked",
                "job_id": job_id,
                "job_status": job_status,
                "timestamp": datetime.now().isoformat(),
            }
        else:
            return create_error_response(
                "JobNotFound",
                f"Job {job_id} not found",
            )
    
    # Wait for job completion (run in executor)
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None,
        lambda: wait_for_job(
            job_id=job_id,
            timeout_seconds=timeout_seconds,
            poll_interval=poll_interval,
        ),
    )
    
    return result


async def handle_analyze_log(arguments: dict[str, Any]) -> dict[str, Any]:
    """Handle analyze_log tool call.
    
    Args:
        arguments: Tool arguments containing job_id, path, or mode
        
    Returns:
        Log analysis result
    """
    job_id = arguments.get("job_id")
    path = arguments.get("path")
    mode = arguments.get("mode", "auto")
    recent_errors = arguments.get("recent_errors", False)
    
    project_root = get_project_root()
    loop = asyncio.get_event_loop()
    
    if recent_errors:
        # Analyze recent error logs
        logs_dir = project_root / "logs" / "slurm"
        results = []
        
        if logs_dir.exists():
            err_files = sorted(logs_dir.glob("*.err"), reverse=True)[:5]
            for err_file in err_files:
                if err_file.stat().st_size > 0:
                    analysis = await loop.run_in_executor(
                        None,
                        lambda f=err_file: analyze_log_file(f, mode="error"),
                    )
                    if analysis.get("conclusion", {}).get("has_errors"):
                        results.append(analysis)
        
        return {
            "status": "success",
            "analyzed_count": len(results),
            "logs": results,
            "timestamp": datetime.now().isoformat(),
        }
    
    elif job_id:
        # Find and analyze logs by job ID
        log_files = await loop.run_in_executor(
            None,
            lambda: find_log_by_job_id(job_id),
        )
        
        if not log_files:
            return create_error_response(
                "FileNotFoundError",
                f"No logs found for job ID {job_id}",
            )
        
        results = []
        for f in log_files:
            analysis = await loop.run_in_executor(
                None,
                lambda log_f=f: analyze_log_file(log_f, mode=mode),
            )
            results.append(analysis)
        
        return {
            "status": "success",
            "job_id": job_id,
            "files": results,
            "timestamp": datetime.now().isoformat(),
        }
    
    elif path:
        # Analyze specific log file
        log_path = Path(path)
        if not log_path.is_absolute():
            log_path = project_root / log_path
        
        result = await loop.run_in_executor(
            None,
            lambda: analyze_log_file(log_path, mode=mode),
        )
        return result
    
    else:
        return create_error_response(
            "ValidationError",
            "At least one of 'job_id', 'path', or 'recent_errors' must be provided",
        )


async def handle_get_status(arguments: dict[str, Any]) -> dict[str, Any]:
    """Handle get_status tool call.
    
    Args:
        arguments: Tool arguments containing detailed, section, no_cache
        
    Returns:
        Project status
    """
    detailed = arguments.get("detailed", False)
    section = arguments.get("section")
    # no_cache is not used in function call as we always fetch fresh in MCP
    
    loop = asyncio.get_event_loop()
    
    if section:
        # Import section-specific functions
        from tools.agent_tools.get_status import (
            get_slurm_jobs,
            get_gpu_status,
            get_recent_results,
            get_error_logs,
            get_pending_tasks,
            get_disk_usage,
        )
        
        result: dict[str, Any] = {"timestamp": datetime.now().isoformat()}
        
        if section == "jobs":
            result["jobs"] = await loop.run_in_executor(None, get_slurm_jobs)
        elif section == "gpu":
            result["gpu"] = await loop.run_in_executor(None, get_gpu_status)
        elif section == "results":
            result["results"] = await loop.run_in_executor(None, get_recent_results)
        elif section == "errors":
            result["errors"] = await loop.run_in_executor(None, get_error_logs)
        elif section == "tasks":
            result["tasks"] = await loop.run_in_executor(None, get_pending_tasks)
        elif section == "disk":
            result["disk"] = await loop.run_in_executor(None, get_disk_usage)
        
        return result
    
    # Full status
    result = await loop.run_in_executor(
        None,
        lambda: get_project_status(detailed=detailed),
    )
    return result


async def handle_save_result(arguments: dict[str, Any]) -> dict[str, Any]:
    """Handle save_result tool call.
    
    Args:
        arguments: Tool arguments containing name, metrics, config, etc.
        
    Returns:
        Save result status
    """
    name = arguments.get("name")
    if not name:
        return create_error_response(
            "ValidationError",
            "Required parameter 'name' is missing",
        )
    
    status = arguments.get("status", "success")
    config = arguments.get("config")
    metrics = arguments.get("metrics")
    baseline = arguments.get("baseline")
    notes = arguments.get("notes")
    output_dir = arguments.get("output_dir", "results")
    dry_run = arguments.get("dry_run", False)
    
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None,
        lambda: save_experiment_result(
            experiment_name=name,
            status=status,
            config=config,
            metrics=metrics,
            baseline_experiment=baseline,
            notes=notes,
            output_dir=output_dir,
            dry_run=dry_run,
        ),
    )
    
    return result


async def handle_compare_results(arguments: dict[str, Any]) -> dict[str, Any]:
    """Handle compare_results tool call.
    
    Args:
        arguments: Tool arguments containing baseline and target paths
        
    Returns:
        Comparison result
    """
    baseline = arguments.get("baseline")
    target = arguments.get("target")
    
    if not baseline:
        return create_error_response(
            "ValidationError",
            "Required parameter 'baseline' is missing",
        )
    
    if not target:
        return create_error_response(
            "ValidationError",
            "Required parameter 'target' is missing",
        )
    
    metrics_only = arguments.get("metrics_only", False)
    project_root = get_project_root()
    
    baseline_path = Path(baseline)
    if not baseline_path.is_absolute():
        baseline_path = project_root / baseline_path
    
    target_path = Path(target)
    if not target_path.is_absolute():
        target_path = project_root / target_path
    
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None,
        lambda: compare_results_impl(
            baseline_path=baseline_path,
            target_path=target_path,
            metrics_only=metrics_only,
        ),
    )
    
    return result


async def handle_validate_config(arguments: dict[str, Any]) -> dict[str, Any]:
    """Handle validate_config tool call.
    
    Args:
        arguments: Tool arguments containing config_path and strict flag
        
    Returns:
        Validation result
    """
    config_path = arguments.get("config_path")
    if not config_path:
        return create_error_response(
            "ValidationError",
            "Required parameter 'config_path' is missing",
        )
    
    strict = arguments.get("strict", False)
    project_root = get_project_root()
    
    path = Path(config_path)
    if not path.is_absolute():
        path = project_root / path
    
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None,
        lambda: validate_config_impl(config_path=path, strict=strict),
    )
    
    return result


async def main() -> None:
    """Run the SLURM Agent Tools MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


if __name__ == "__main__":
    asyncio.run(main())

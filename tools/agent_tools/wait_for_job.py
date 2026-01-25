#!/usr/bin/env python3
"""Wait for SLURM Job Completion Tool

Waits for a SLURM job to complete and returns the final status.
Supports timeout and polling interval configuration.

Usage:
    uv run python -m tools.agent_tools.wait_for_job --job-id 12345
    uv run python -m tools.agent_tools.wait_for_job --job-id 12345 --timeout 3600
    uv run python -m tools.agent_tools.wait_for_job --job-id 12345 --analyze-on-complete
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml


def get_project_root() -> Path:
    """Return project root directory."""
    return Path(__file__).parent.parent.parent


def load_agent_policy() -> dict[str, Any]:
    """Load agent policy configuration."""
    policy_path = get_project_root() / "configs" / "agent_policy.yaml"
    if policy_path.exists():
        with open(policy_path) as f:
            return yaml.safe_load(f) or {}
    return {}


def get_job_status(job_id: str) -> dict[str, Any] | None:
    """Get status of a specific SLURM job."""
    try:
        # First check squeue for running/pending jobs
        result = subprocess.run(
            ["squeue", "-j", job_id, "-o", "%i,%j,%T,%M,%r", "--noheader"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0 and result.stdout.strip():
            parts = result.stdout.strip().split(",")
            if len(parts) >= 4:
                return {
                    "id": parts[0],
                    "name": parts[1],
                    "state": parts[2],
                    "time": parts[3],
                    "reason": parts[4] if len(parts) > 4 else "",
                    "completed": False,
                }
        
        # Check sacct for completed jobs
        result = subprocess.run(
            [
                "sacct", "-j", job_id,
                "--format", "JobID,JobName,State,ExitCode,Elapsed,Start,End",
                "--noheader", "--parsable2",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0 and result.stdout.strip():
            for line in result.stdout.strip().split("\n"):
                # Skip batch/extern steps
                if ".batch" in line or ".extern" in line:
                    continue
                parts = line.split("|")
                if len(parts) >= 4 and parts[0] == job_id:
                    state = parts[2]
                    return {
                        "id": parts[0],
                        "name": parts[1],
                        "state": state,
                        "exit_code": parts[3],
                        "elapsed": parts[4] if len(parts) > 4 else "",
                        "start_time": parts[5] if len(parts) > 5 else "",
                        "end_time": parts[6] if len(parts) > 6 else "",
                        "completed": True,
                        "success": "COMPLETED" in state,
                        "failed": "FAILED" in state or "CANCELLED" in state or "TIMEOUT" in state,
                    }
        
        return None
        
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return None


def wait_for_job(
    job_id: str,
    timeout_seconds: int = 28800,  # 8 hours default
    poll_interval: int = 30,
) -> dict[str, Any]:
    """Wait for a SLURM job to complete.
    
    Args:
        job_id: SLURM job ID
        timeout_seconds: Maximum wait time in seconds
        poll_interval: Polling interval in seconds
        
    Returns:
        JSON result with final job status
    """
    start_time = time.time()
    last_state = None
    
    while True:
        elapsed = time.time() - start_time
        
        # Check timeout
        if elapsed >= timeout_seconds:
            return {
                "status": "timeout",
                "job_id": job_id,
                "message": f"Timeout after {timeout_seconds}s",
                "last_known_state": last_state,
                "elapsed_seconds": round(elapsed, 1),
                "timestamp": datetime.now().isoformat(),
            }
        
        # Get job status
        job_status = get_job_status(job_id)
        
        if job_status is None:
            return {
                "status": "error",
                "error_type": "JobNotFound",
                "job_id": job_id,
                "message": f"Job {job_id} not found",
                "timestamp": datetime.now().isoformat(),
            }
        
        last_state = job_status["state"]
        
        # Check if completed
        if job_status.get("completed"):
            result: dict[str, Any] = {
                "status": "completed",
                "job_id": job_id,
                "job_status": job_status,
                "elapsed_seconds": round(elapsed, 1),
                "timestamp": datetime.now().isoformat(),
            }
            
            if job_status.get("success"):
                result["outcome"] = "success"
            elif job_status.get("failed"):
                result["outcome"] = "failed"
                result["recommendation"] = "Run analyze_log to investigate the failure"
            
            return result
        
        # Wait before next poll
        time.sleep(poll_interval)


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Wait for SLURM job completion (JSON output)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--job-id",
        type=str,
        required=True,
        help="SLURM job ID to wait for",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=None,
        help="Timeout in seconds (default: from agent_policy.yaml)",
    )
    parser.add_argument(
        "--poll-interval",
        type=int,
        default=None,
        help="Polling interval in seconds (default: from agent_policy.yaml)",
    )
    parser.add_argument(
        "--no-wait",
        action="store_true",
        help="Check status once without waiting",
    )
    
    args = parser.parse_args()
    
    # Load defaults from policy
    policy = load_agent_policy()
    automation = policy.get("automation", {})
    
    timeout = args.timeout or automation.get("max_wait_time_minutes", 480) * 60
    poll_interval = args.poll_interval or automation.get("job_poll_interval_seconds", 30)
    
    if args.no_wait:
        # Just check status once
        job_status = get_job_status(args.job_id)
        if job_status:
            result = {
                "status": "checked",
                "job_id": args.job_id,
                "job_status": job_status,
                "timestamp": datetime.now().isoformat(),
            }
        else:
            result = {
                "status": "error",
                "error_type": "JobNotFound",
                "job_id": args.job_id,
                "message": f"Job {args.job_id} not found",
                "timestamp": datetime.now().isoformat(),
            }
        print(json.dumps(result, indent=2))
    else:
        # Wait for completion
        result = wait_for_job(
            job_id=args.job_id,
            timeout_seconds=timeout,
            poll_interval=poll_interval,
        )
        print(json.dumps(result, indent=2))
        
        if result.get("outcome") == "failed":
            sys.exit(1)


if __name__ == "__main__":
    main()

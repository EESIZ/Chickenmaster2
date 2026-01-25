#!/usr/bin/env python3
"""SLURM Job Submission Tool

Wrapper for submitting SLURM jobs safely with JSON output.
All outputs are JSON-formatted for easy parsing by AI agents.

Usage:
    uv run python -m tools.agent_tools.submit_job --script run_experiment.sh
    uv run python -m tools.agent_tools.submit_job --job-name test --script run_experiment.sh
    uv run python -m tools.agent_tools.submit_job --config configs/exp.yaml --dry-run
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
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


def get_active_jobs() -> list[dict[str, Any]]:
    """Get list of currently active SLURM jobs."""
    try:
        result = subprocess.run(
            ["squeue", "-u", os.environ.get("USER", ""), "-o", "%i,%j,%T,%M"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            return []
        
        jobs = []
        lines = result.stdout.strip().split("\n")[1:]  # Skip header
        for line in lines:
            if line.strip():
                parts = line.split(",")
                if len(parts) >= 4:
                    jobs.append({
                        "id": parts[0],
                        "name": parts[1],
                        "state": parts[2],
                        "time": parts[3],
                    })
        return jobs
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return []


def check_safety_limits(policy: dict[str, Any]) -> dict[str, Any]:
    """Check safety limits before job submission."""
    limits = policy.get("limits", {})
    max_active_jobs = limits.get("max_active_jobs", 10)
    
    active_jobs = get_active_jobs()
    current_count = len(active_jobs)
    
    if current_count >= max_active_jobs:
        return {
            "allowed": False,
            "reason": f"Max active jobs exceeded: {current_count}/{max_active_jobs}",
            "active_jobs": active_jobs,
        }
    
    return {
        "allowed": True,
        "current_active_jobs": current_count,
        "max_active_jobs": max_active_jobs,
    }


def submit_slurm_job(
    script_path: str,
    job_name: str | None = None,
    args: list[str] | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Submit a SLURM job.
    
    Args:
        script_path: Path to SLURM script (relative to scripts/slurm/)
        job_name: Optional job name
        args: Optional additional arguments
        dry_run: If True, return command without executing
        
    Returns:
        JSON-formatted result
    """
    project_root = get_project_root()
    full_script_path = project_root / "scripts" / "slurm" / script_path
    
    if not full_script_path.exists():
        return {
            "status": "error",
            "error_type": "FileNotFoundError",
            "message": f"Script not found: {full_script_path}",
            "timestamp": datetime.now().isoformat(),
        }
    
    # Build command
    cmd = ["sbatch"]
    if job_name:
        cmd.extend(["--job-name", job_name])
    cmd.append(str(full_script_path))
    if args:
        cmd.extend(args)
    
    command_str = " ".join(cmd)
    
    if dry_run:
        return {
            "status": "dry_run",
            "command": command_str,
            "timestamp": datetime.now().isoformat(),
        }
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=project_root,
            timeout=60,
        )
        
        if result.returncode == 0:
            # Extract Job ID from output: "Submitted batch job 12345"
            output = result.stdout.strip()
            job_id = None
            if "Submitted batch job" in output:
                job_id = output.split()[-1]
            
            log_path = f"logs/slurm/{job_name or 'job'}_{job_id}.out" if job_id else None
            
            return {
                "status": "success",
                "job_id": job_id,
                "log_path": log_path,
                "error_log_path": log_path.replace(".out", ".err") if log_path else None,
                "command_executed": command_str,
                "stdout": output,
                "timestamp": datetime.now().isoformat(),
            }
        else:
            return {
                "status": "error",
                "error_type": "SlurmSubmissionError",
                "message": result.stderr.strip() or "Job submission failed",
                "command_executed": command_str,
                "return_code": result.returncode,
                "timestamp": datetime.now().isoformat(),
            }
            
    except subprocess.TimeoutExpired:
        return {
            "status": "error",
            "error_type": "TimeoutError",
            "message": "Job submission timed out (60s)",
            "command_executed": command_str,
            "timestamp": datetime.now().isoformat(),
        }
    except FileNotFoundError:
        return {
            "status": "error",
            "error_type": "SlurmNotFound",
            "message": "SLURM (sbatch) not found in PATH",
            "timestamp": datetime.now().isoformat(),
        }


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="SLURM job submission tool (JSON output)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--script",
        type=str,
        default="run_experiment.sh",
        help="SLURM script to run (relative to scripts/slurm/)",
    )
    parser.add_argument(
        "--job-name",
        type=str,
        help="SLURM job name",
    )
    parser.add_argument(
        "--args",
        type=str,
        help="Additional arguments (space-separated)",
    )
    parser.add_argument(
        "--config",
        type=str,
        help="Experiment config file path (YAML)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print command without executing",
    )
    parser.add_argument(
        "--skip-safety-check",
        action="store_true",
        help="Skip safety checks (not recommended)",
    )
    
    args = parser.parse_args()
    
    # Safety check
    if not args.skip_safety_check:
        policy = load_agent_policy()
        safety_check = check_safety_limits(policy)
        
        if not safety_check.get("allowed", True):
            result = {
                "status": "blocked",
                "reason": safety_check["reason"],
                "active_jobs": safety_check.get("active_jobs", []),
                "timestamp": datetime.now().isoformat(),
            }
            print(json.dumps(result, indent=2))
            sys.exit(1)
    
    # Extract job name from config if not provided
    job_name = args.job_name
    if args.config and not job_name:
        config_path = get_project_root() / args.config
        if config_path.exists():
            with open(config_path) as f:
                config = yaml.safe_load(f) or {}
                job_name = config.get("experiment", {}).get("name")
    
    # Parse arguments
    script_args = args.args.split() if args.args else None
    
    # Submit job
    result = submit_slurm_job(
        script_path=args.script,
        job_name=job_name,
        args=script_args,
        dry_run=args.dry_run,
    )
    
    print(json.dumps(result, indent=2))
    
    if result["status"] == "error":
        sys.exit(1)


if __name__ == "__main__":
    main()

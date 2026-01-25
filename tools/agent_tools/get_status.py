#!/usr/bin/env python3
"""Project Status Query Tool

Provides a comprehensive view of project status in JSON format.
Includes SLURM jobs, GPU status, recent results, and errors.
Supports caching to reduce repeated queries.

Usage:
    uv run python -m tools.agent_tools.get_status
    uv run python -m tools.agent_tools.get_status --detailed
    uv run python -m tools.agent_tools.get_status --section jobs
    uv run python -m tools.agent_tools.get_status --no-cache
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

# Cache configuration
CACHE_FILE = ".project_status_cache.json"
CACHE_TTL_SECONDS = 60  # 1 minute


def get_project_root() -> Path:
    """Return project root directory."""
    return Path(__file__).parent.parent.parent


def load_cache() -> dict[str, Any] | None:
    """Load cached status if valid."""
    cache_path = get_project_root() / CACHE_FILE
    if not cache_path.exists():
        return None
    
    try:
        with open(cache_path) as f:
            cache = json.load(f)
        
        # Check TTL
        cached_time = datetime.fromisoformat(cache.get("timestamp", ""))
        if (datetime.now() - cached_time).total_seconds() < CACHE_TTL_SECONDS:
            cache["from_cache"] = True
            return cache
    except (json.JSONDecodeError, OSError, ValueError):
        pass
    
    return None


def save_cache(status: dict[str, Any]) -> None:
    """Save status to cache file."""
    cache_path = get_project_root() / CACHE_FILE
    try:
        with open(cache_path, "w") as f:
            json.dump(status, f, indent=2)
    except OSError:
        pass  # Ignore cache write errors


def get_slurm_jobs() -> dict[str, Any]:
    """Query SLURM job status."""
    jobs: dict[str, Any] = {
        "running": [],
        "pending": [],
        "completed_today": [],
        "failed_today": [],
    }
    
    try:
        # Running/pending jobs
        result = subprocess.run(
            ["squeue", "-u", os.environ.get("USER", ""), "-o", "%i,%j,%T,%M,%S,%e"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            lines = result.stdout.strip().split("\n")[1:]
            for line in lines:
                if line.strip():
                    parts = line.split(",")
                    if len(parts) >= 4:
                        job_info = {
                            "id": parts[0],
                            "name": parts[1],
                            "state": parts[2],
                            "time": parts[3],
                        }
                        if parts[2] == "RUNNING":
                            jobs["running"].append(job_info)
                        elif parts[2] == "PENDING":
                            jobs["pending"].append(job_info)
        
        # Recently completed jobs (using sacct)
        today = datetime.now().strftime("%Y-%m-%d")
        result = subprocess.run(
            [
                "sacct", "-u", os.environ.get("USER", ""),
                "--starttime", today,
                "--format", "JobID,JobName,State,ExitCode,Elapsed",
                "--noheader", "--parsable2",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            for line in result.stdout.strip().split("\n"):
                if line.strip() and ".batch" not in line and ".extern" not in line:
                    parts = line.split("|")
                    if len(parts) >= 4:
                        job_info = {
                            "id": parts[0],
                            "name": parts[1],
                            "state": parts[2],
                            "exit_code": parts[3] if len(parts) > 3 else "",
                        }
                        if "COMPLETED" in parts[2]:
                            jobs["completed_today"].append(job_info)
                        elif "FAILED" in parts[2] or "CANCELLED" in parts[2]:
                            jobs["failed_today"].append(job_info)
                            
    except (subprocess.TimeoutExpired, FileNotFoundError):
        jobs["slurm_available"] = False
        
    jobs["total_active"] = len(jobs["running"]) + len(jobs["pending"])
    return jobs


def get_gpu_status() -> dict[str, Any]:
    """Query GPU status."""
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=index,name,memory.used,memory.total,utilization.gpu",
             "--format=csv,noheader,nounits"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            gpus = []
            for line in result.stdout.strip().split("\n"):
                if line.strip():
                    parts = [p.strip() for p in line.split(",")]
                    if len(parts) >= 5:
                        gpus.append({
                            "index": int(parts[0]),
                            "name": parts[1],
                            "memory_used_mb": int(parts[2]),
                            "memory_total_mb": int(parts[3]),
                            "utilization_percent": int(parts[4]),
                        })
            return {
                "available": True,
                "count": len(gpus),
                "gpus": gpus,
            }
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    
    return {"available": False, "count": 0, "gpus": []}


def get_recent_results(days: int = 7) -> list[dict[str, Any]]:
    """Get recent experiment results."""
    results_dir = get_project_root() / "results"
    if not results_dir.exists():
        return []
    
    cutoff = datetime.now() - timedelta(days=days)
    recent_results = []
    
    for json_file in results_dir.rglob("*.json"):
        try:
            mtime = datetime.fromtimestamp(json_file.stat().st_mtime)
            if mtime >= cutoff:
                recent_results.append({
                    "path": str(json_file.relative_to(get_project_root())),
                    "modified": mtime.isoformat(),
                    "size_bytes": json_file.stat().st_size,
                })
        except OSError:
            continue
    
    recent_results.sort(key=lambda x: x["modified"], reverse=True)
    return recent_results[:20]


def get_error_logs() -> list[dict[str, Any]]:
    """Detect error log files."""
    logs_dir = get_project_root() / "logs" / "slurm"
    if not logs_dir.exists():
        return []
    
    error_logs = []
    error_keywords = ["Error", "Exception", "Traceback", "FAILED", "OOM", "CUDA error"]
    
    for err_file in logs_dir.glob("*.err"):
        try:
            content = err_file.read_text(errors="ignore")
            if any(keyword in content for keyword in error_keywords):
                if err_file.stat().st_size > 0:
                    error_logs.append({
                        "path": str(err_file.relative_to(get_project_root())),
                        "size_bytes": err_file.stat().st_size,
                        "modified": datetime.fromtimestamp(
                            err_file.stat().st_mtime
                        ).isoformat(),
                    })
        except OSError:
            continue
    
    error_logs.sort(key=lambda x: x["modified"], reverse=True)
    return error_logs[:10]


def get_pending_tasks() -> list[dict[str, Any]]:
    """Parse pending tasks from todo.md."""
    todo_path = get_project_root() / "documents" / "todo.md"
    tasks = []
    
    if todo_path.exists():
        try:
            content = todo_path.read_text()
            lines = content.split("\n")
            current_section = ""
            
            for line in lines:
                line = line.strip()
                if line.startswith("## "):
                    current_section = line[3:].strip()
                elif line.startswith("- [ ]"):
                    task_text = line[5:].strip()
                    tasks.append({
                        "section": current_section,
                        "task": task_text,
                        "status": "pending",
                    })
        except OSError:
            pass
    
    return tasks[:20]


def get_disk_usage() -> dict[str, Any]:
    """Get disk usage statistics."""
    project_root = get_project_root()
    
    def get_dir_size(path: Path) -> int:
        total = 0
        try:
            for item in path.rglob("*"):
                if item.is_file():
                    total += item.stat().st_size
        except OSError:
            pass
        return total
    
    return {
        "results_mb": round(get_dir_size(project_root / "results") / 1024 / 1024, 2),
        "logs_mb": round(get_dir_size(project_root / "logs") / 1024 / 1024, 2),
        "resource_mb": round(get_dir_size(project_root / "resource") / 1024 / 1024, 2),
    }


def get_project_status(detailed: bool = False) -> dict[str, Any]:
    """Get comprehensive project status."""
    status: dict[str, Any] = {
        "timestamp": datetime.now().isoformat(),
        "project_root": str(get_project_root()),
    }
    
    # SLURM jobs
    jobs = get_slurm_jobs()
    status["jobs"] = {
        "running_count": len(jobs["running"]),
        "pending_count": len(jobs["pending"]),
        "running": jobs["running"],
        "pending": jobs["pending"],
    }
    
    if detailed:
        status["jobs"]["completed_today"] = jobs["completed_today"]
        status["jobs"]["failed_today"] = jobs["failed_today"]
    
    # GPU status
    status["gpu"] = get_gpu_status()
    
    # Recent results
    status["recent_results"] = get_recent_results(days=3)
    
    # Error logs
    error_logs = get_error_logs()
    status["errors"] = {
        "count": len(error_logs),
        "logs": error_logs,
    }
    
    # Pending tasks
    if detailed:
        status["pending_tasks"] = get_pending_tasks()
    
    # Disk usage
    if detailed:
        status["disk_usage"] = get_disk_usage()
    
    # Summary
    status["summary"] = {
        "active_jobs": jobs["total_active"],
        "recent_errors": len(error_logs),
        "recent_results": len(status["recent_results"]),
        "needs_attention": len(error_logs) > 0 or len(jobs.get("failed_today", [])) > 0,
    }
    
    return status


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Project status query tool (JSON output)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--detailed",
        action="store_true",
        help="Include detailed information",
    )
    parser.add_argument(
        "--section",
        type=str,
        choices=["jobs", "gpu", "results", "errors", "tasks", "disk"],
        help="Query specific section only",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Bypass cache and fetch fresh data",
    )
    parser.add_argument(
        "--clear-cache",
        action="store_true",
        help="Clear the cache file",
    )
    
    args = parser.parse_args()
    
    # Clear cache if requested
    if args.clear_cache:
        cache_path = get_project_root() / CACHE_FILE
        if cache_path.exists():
            cache_path.unlink()
        print(json.dumps({"status": "cache_cleared", "timestamp": datetime.now().isoformat()}, indent=2))
        return
    
    if args.section:
        # Section queries bypass cache
        result: dict[str, Any] = {"timestamp": datetime.now().isoformat()}
        
        if args.section == "jobs":
            result["jobs"] = get_slurm_jobs()
        elif args.section == "gpu":
            result["gpu"] = get_gpu_status()
        elif args.section == "results":
            result["results"] = get_recent_results()
        elif args.section == "errors":
            result["errors"] = get_error_logs()
        elif args.section == "tasks":
            result["tasks"] = get_pending_tasks()
        elif args.section == "disk":
            result["disk"] = get_disk_usage()
            
        print(json.dumps(result, indent=2))
    else:
        # Try cache first (unless --no-cache or --detailed)
        if not args.no_cache and not args.detailed:
            cached = load_cache()
            if cached:
                print(json.dumps(cached, indent=2))
                return
        
        # Fetch fresh status
        status = get_project_status(detailed=args.detailed)
        
        # Save to cache (only for non-detailed queries)
        if not args.detailed:
            save_cache(status)
        
        print(json.dumps(status, indent=2))


if __name__ == "__main__":
    main()

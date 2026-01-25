#!/usr/bin/env python3
"""Log Analysis and Error Summary Tool

Extracts important information from log files efficiently.
Helps AI agents quickly identify and understand errors.

Usage:
    uv run python -m tools.agent_tools.analyze_log --path logs/slurm/exp_123.out
    uv run python -m tools.agent_tools.analyze_log --job-id 12345
    uv run python -m tools.agent_tools.analyze_log --recent-errors
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


def get_project_root() -> Path:
    """Return project root directory."""
    return Path(__file__).parent.parent.parent


# Error/Warning patterns
ERROR_PATTERNS = [
    (r"Error:?\s*(.+)", "error"),
    (r"Exception:?\s*(.+)", "exception"),
    (r"Traceback \(most recent call last\)", "traceback"),
    (r"CUDA out of memory", "oom"),
    (r"CUDA error", "cuda_error"),
    (r"RuntimeError:?\s*(.+)", "runtime_error"),
    (r"ValueError:?\s*(.+)", "value_error"),
    (r"KeyError:?\s*(.+)", "key_error"),
    (r"FileNotFoundError:?\s*(.+)", "file_not_found"),
    (r"ModuleNotFoundError:?\s*(.+)", "module_not_found"),
    (r"ImportError:?\s*(.+)", "import_error"),
    (r"AssertionError:?\s*(.+)", "assertion_error"),
    (r"FAILED", "failed"),
    (r"CANCELLED", "cancelled"),
    (r"slurmstepd: error:?\s*(.+)", "slurm_error"),
]

WARNING_PATTERNS = [
    (r"Warning:?\s*(.+)", "warning"),
    (r"UserWarning:?\s*(.+)", "user_warning"),
    (r"DeprecationWarning:?\s*(.+)", "deprecation_warning"),
    (r"FutureWarning:?\s*(.+)", "future_warning"),
]

# Metric patterns
METRIC_PATTERNS = [
    (r"loss[:\s=]+([0-9.e+-]+)", "loss"),
    (r"accuracy[:\s=]+([0-9.e+-]+)", "accuracy"),
    (r"acc[:\s=]+([0-9.e+-]+)", "accuracy"),
    (r"f1[:\s=]+([0-9.e+-]+)", "f1"),
    (r"precision[:\s=]+([0-9.e+-]+)", "precision"),
    (r"recall[:\s=]+([0-9.e+-]+)", "recall"),
    (r"epoch[:\s=]+(\d+)", "epoch"),
    (r"step[:\s=]+(\d+)", "step"),
    (r"lr[:\s=]+([0-9.e+-]+)", "learning_rate"),
    (r"learning_rate[:\s=]+([0-9.e+-]+)", "learning_rate"),
]


def extract_context_lines(
    lines: list[str],
    target_idx: int,
    context_before: int = 5,
    context_after: int = 15,
) -> list[str]:
    """Extract context lines around target line."""
    start = max(0, target_idx - context_before)
    end = min(len(lines), target_idx + context_after + 1)
    return lines[start:end]


def analyze_errors(content: str) -> dict[str, Any]:
    """Analyze errors and exceptions."""
    lines = content.split("\n")
    errors = []
    seen_errors: set[str] = set()
    
    for i, line in enumerate(lines):
        for pattern, error_type in ERROR_PATTERNS:
            if re.search(pattern, line, re.IGNORECASE):
                error_key = f"{error_type}:{line[:100]}"
                if error_key in seen_errors:
                    continue
                seen_errors.add(error_key)
                
                context = extract_context_lines(lines, i)
                errors.append({
                    "type": error_type,
                    "line_number": i + 1,
                    "message": line.strip(),
                    "context": "\n".join(context),
                })
                break
    
    return {
        "count": len(errors),
        "errors": errors[:10],
    }


def analyze_warnings(content: str) -> dict[str, Any]:
    """Analyze warnings."""
    lines = content.split("\n")
    warnings = []
    warning_counts: dict[str, int] = {}
    
    for i, line in enumerate(lines):
        for pattern, warning_type in WARNING_PATTERNS:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                warning_counts[warning_type] = warning_counts.get(warning_type, 0) + 1
                if len(warnings) < 5:
                    warnings.append({
                        "type": warning_type,
                        "line_number": i + 1,
                        "message": line.strip()[:200],
                    })
                break
    
    return {
        "total_count": sum(warning_counts.values()),
        "by_type": warning_counts,
        "samples": warnings,
    }


def extract_metrics(content: str) -> dict[str, Any]:
    """Extract training metrics."""
    metrics: dict[str, Any] = {}
    
    for pattern, metric_name in METRIC_PATTERNS:
        matches = re.findall(pattern, content, re.IGNORECASE)
        if matches:
            values = []
            for m in matches[-10:]:
                try:
                    values.append(float(m))
                except ValueError:
                    continue
            if values:
                metrics[metric_name] = {
                    "last": values[-1],
                    "min": min(values),
                    "max": max(values),
                    "count": len(matches),
                }
    
    return metrics


def get_log_summary(content: str) -> dict[str, Any]:
    """Extract log summary information."""
    lines = content.split("\n")
    
    start_time = None
    end_time = None
    time_pattern = r"(\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2})"
    
    for line in lines[:50]:
        match = re.search(time_pattern, line)
        if match:
            start_time = match.group(1)
            break
    
    for line in reversed(lines[-50:]):
        match = re.search(time_pattern, line)
        if match:
            end_time = match.group(1)
            break
    
    return {
        "total_lines": len(lines),
        "start_time": start_time,
        "end_time": end_time,
        "first_lines": "\n".join(lines[:5]),
        "last_lines": "\n".join(lines[-10:]),
    }


def analyze_log_file(log_path: Path, mode: str = "auto") -> dict[str, Any]:
    """Analyze a log file."""
    if not log_path.exists():
        return {
            "status": "error",
            "error_type": "FileNotFoundError",
            "message": f"Log file not found: {log_path}",
            "timestamp": datetime.now().isoformat(),
        }
    
    try:
        content = log_path.read_text(errors="ignore")
    except OSError as e:
        return {
            "status": "error",
            "error_type": "IOError",
            "message": f"Failed to read file: {e}",
            "timestamp": datetime.now().isoformat(),
        }
    
    result: dict[str, Any] = {
        "status": "success",
        "file_path": str(log_path),
        "file_size_kb": round(log_path.stat().st_size / 1024, 2),
        "timestamp": datetime.now().isoformat(),
    }
    
    # Auto-detect mode
    if mode == "auto":
        if log_path.suffix == ".err" or "error" in log_path.name.lower():
            mode = "error"
        else:
            mode = "full"
    
    if mode == "error":
        result["errors"] = analyze_errors(content)
        result["summary"] = get_log_summary(content)
    elif mode == "metrics":
        result["metrics"] = extract_metrics(content)
        result["summary"] = get_log_summary(content)
    else:  # full
        result["summary"] = get_log_summary(content)
        result["errors"] = analyze_errors(content)
        result["warnings"] = analyze_warnings(content)
        result["metrics"] = extract_metrics(content)
    
    # Add conclusion
    error_count = result.get("errors", {}).get("count", 0)
    result["conclusion"] = {
        "has_errors": error_count > 0,
        "error_count": error_count,
        "primary_error": result.get("errors", {}).get("errors", [{}])[0].get("type")
        if error_count > 0 else None,
        "needs_attention": error_count > 0,
    }
    
    return result


def find_log_by_job_id(job_id: str) -> list[Path]:
    """Find log files by job ID."""
    logs_dir = get_project_root() / "logs" / "slurm"
    if not logs_dir.exists():
        return []
    
    return list(logs_dir.glob(f"*_{job_id}.*"))


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Log analysis and error summary tool (JSON output)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--path",
        type=str,
        help="Log file path to analyze",
    )
    parser.add_argument(
        "--job-id",
        type=str,
        help="Find logs by SLURM job ID",
    )
    parser.add_argument(
        "--mode",
        type=str,
        choices=["auto", "error", "metrics", "full"],
        default="auto",
        help="Analysis mode (default: auto)",
    )
    parser.add_argument(
        "--recent-errors",
        action="store_true",
        help="Analyze all recent error logs",
    )
    
    args = parser.parse_args()
    project_root = get_project_root()
    
    if args.recent_errors:
        logs_dir = project_root / "logs" / "slurm"
        results = []
        
        for err_file in sorted(logs_dir.glob("*.err"), reverse=True)[:5]:
            if err_file.stat().st_size > 0:
                analysis = analyze_log_file(err_file, mode="error")
                if analysis.get("conclusion", {}).get("has_errors"):
                    results.append(analysis)
        
        print(json.dumps({
            "status": "success",
            "analyzed_count": len(results),
            "logs": results,
            "timestamp": datetime.now().isoformat(),
        }, indent=2))
        
    elif args.job_id:
        log_files = find_log_by_job_id(args.job_id)
        
        if not log_files:
            print(json.dumps({
                "status": "error",
                "error_type": "FileNotFoundError",
                "message": f"No logs found for job ID {args.job_id}",
                "timestamp": datetime.now().isoformat(),
            }, indent=2))
            sys.exit(1)
        
        results = [analyze_log_file(f, mode=args.mode) for f in log_files]
        
        print(json.dumps({
            "status": "success",
            "job_id": args.job_id,
            "files": results,
            "timestamp": datetime.now().isoformat(),
        }, indent=2))
        
    elif args.path:
        log_path = Path(args.path)
        if not log_path.is_absolute():
            log_path = project_root / log_path
        
        result = analyze_log_file(log_path, mode=args.mode)
        print(json.dumps(result, indent=2))
        
        if result["status"] == "error":
            sys.exit(1)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()

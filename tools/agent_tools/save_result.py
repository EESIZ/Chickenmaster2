#!/usr/bin/env python3
"""Experiment Result Save Utility

Saves experiment results with standardized schema and validation.
Automatically adds metadata and computes config diffs.

Usage:
    uv run python -m tools.agent_tools.save_result --name "exp_001" --metrics '{"loss": 0.1}'
    uv run python -m tools.agent_tools.save_result --config configs/exp.yaml --baseline results/prev.json
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml


def get_project_root() -> Path:
    """Return project root directory."""
    return Path(__file__).parent.parent.parent


def get_git_info() -> dict[str, str | bool | None]:
    """Get git repository information."""
    info: dict[str, str | bool | None] = {
        "commit": None,
        "branch": None,
        "dirty": None,
    }
    
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            cwd=get_project_root(),
            timeout=10,
        )
        if result.returncode == 0:
            info["commit"] = result.stdout.strip()[:8]
        
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            cwd=get_project_root(),
            timeout=10,
        )
        if result.returncode == 0:
            info["branch"] = result.stdout.strip()
        
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            cwd=get_project_root(),
            timeout=10,
        )
        if result.returncode == 0:
            info["dirty"] = bool(result.stdout.strip())
            
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    
    return info


def get_environment_info() -> dict[str, Any]:
    """Get environment information."""
    env_info: dict[str, Any] = {
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "hostname": platform.node(),
    }
    
    # GPU info
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            gpus = [g.strip() for g in result.stdout.strip().split("\n") if g.strip()]
            env_info["gpu"] = gpus[0] if len(gpus) == 1 else gpus
    except (subprocess.TimeoutExpired, FileNotFoundError):
        env_info["gpu"] = None
    
    # SLURM info
    slurm_job_id = os.environ.get("SLURM_JOB_ID")
    if slurm_job_id:
        env_info["slurm_job_id"] = slurm_job_id
        env_info["slurm_node"] = os.environ.get("SLURM_NODELIST")
    
    return env_info


def compute_config_diff(
    current_config: dict[str, Any],
    baseline_path: str | None = None,
) -> dict[str, Any] | None:
    """Compute configuration differences from baseline."""
    if not baseline_path:
        return None
    
    baseline_file = get_project_root() / baseline_path
    if not baseline_file.exists():
        return None
    
    try:
        with open(baseline_file) as f:
            baseline_result = json.load(f)
        baseline_config = baseline_result.get("config", {})
    except (json.JSONDecodeError, OSError):
        return None
    
    def flatten_dict(d: dict[str, Any], prefix: str = "") -> dict[str, Any]:
        """Flatten nested dictionary."""
        items: dict[str, Any] = {}
        for k, v in d.items():
            key = f"{prefix}.{k}" if prefix else k
            if isinstance(v, dict):
                items.update(flatten_dict(v, key))
            else:
                items[key] = v
        return items
    
    flat_current = flatten_dict(current_config)
    flat_baseline = flatten_dict(baseline_config)
    
    diff: dict[str, dict[str, Any]] = {}
    
    all_keys = set(flat_current.keys()) | set(flat_baseline.keys())
    for key in all_keys:
        current_val = flat_current.get(key)
        baseline_val = flat_baseline.get(key)
        
        if current_val != baseline_val:
            diff[key] = {
                "from": baseline_val,
                "to": current_val,
            }
    
    return diff if diff else None


def validate_result(result: dict[str, Any]) -> list[str]:
    """Validate result schema."""
    errors = []
    
    required_fields = ["experiment_name", "timestamp", "status"]
    for field in required_fields:
        if field not in result:
            errors.append(f"Missing required field: {field}")
    
    valid_statuses = ["success", "failed", "cancelled"]
    if result.get("status") and result["status"] not in valid_statuses:
        errors.append(f"Invalid status: {result['status']} (allowed: {valid_statuses})")
    
    if result.get("timestamp"):
        try:
            datetime.fromisoformat(result["timestamp"].replace("Z", "+00:00"))
        except ValueError:
            errors.append(f"Invalid timestamp format: {result['timestamp']}")
    
    return errors


def save_experiment_result(
    experiment_name: str,
    status: str = "success",
    config: dict[str, Any] | None = None,
    metrics: dict[str, Any] | None = None,
    baseline_experiment: str | None = None,
    notes: str | None = None,
    output_dir: str = "results",
    dry_run: bool = False,
) -> dict[str, Any]:
    """Save experiment result.
    
    Args:
        experiment_name: Experiment name
        status: Experiment status (success, failed, cancelled)
        config: Experiment configuration
        metrics: Experiment metrics
        baseline_experiment: Baseline experiment file path for diff
        notes: Experiment notes
        output_dir: Output directory
        dry_run: If True, return result without saving
        
    Returns:
        JSON result
    """
    timestamp = datetime.now()
    
    result: dict[str, Any] = {
        "experiment_name": experiment_name,
        "timestamp": timestamp.isoformat(),
        "status": status,
    }
    
    if config:
        result["config"] = config
    
    if metrics:
        result["metrics"] = metrics
    
    # Compute config diff
    if baseline_experiment and config:
        diff = compute_config_diff(config, baseline_experiment)
        if diff:
            result["config_diff"] = diff
            result["baseline_experiment"] = baseline_experiment
    
    # Add environment info
    result["environment"] = get_environment_info()
    result["environment"]["git"] = get_git_info()
    
    if notes:
        result["notes"] = notes
    
    # Validate
    validation_errors = validate_result(result)
    if validation_errors:
        return {
            "status": "error",
            "error_type": "ValidationError",
            "message": "Result validation failed",
            "validation_errors": validation_errors,
            "timestamp": timestamp.isoformat(),
        }
    
    if dry_run:
        return {
            "status": "dry_run",
            "result": result,
            "timestamp": timestamp.isoformat(),
        }
    
    # Save
    project_root = get_project_root()
    output_path = project_root / output_dir
    output_path.mkdir(parents=True, exist_ok=True)
    
    filename = f"{timestamp.strftime('%Y-%m-%d_%H-%M-%S')}_{experiment_name}.json"
    file_path = output_path / filename
    
    try:
        with open(file_path, "w") as f:
            json.dump(result, f, indent=2)
        
        return {
            "status": "success",
            "file_path": str(file_path.relative_to(project_root)),
            "experiment_name": experiment_name,
            "timestamp": timestamp.isoformat(),
        }
    except OSError as e:
        return {
            "status": "error",
            "error_type": "IOError",
            "message": f"Failed to save file: {e}",
            "timestamp": timestamp.isoformat(),
        }


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Experiment result save tool (JSON output)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--name",
        type=str,
        required=True,
        help="Experiment name",
    )
    parser.add_argument(
        "--status",
        type=str,
        choices=["success", "failed", "cancelled"],
        default="success",
        help="Experiment status",
    )
    parser.add_argument(
        "--config",
        type=str,
        help="Config file path (YAML or JSON)",
    )
    parser.add_argument(
        "--metrics",
        type=str,
        help="Metrics (JSON string or file path)",
    )
    parser.add_argument(
        "--baseline",
        type=str,
        help="Baseline experiment result file path",
    )
    parser.add_argument(
        "--notes",
        type=str,
        help="Experiment notes",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="results",
        help="Output directory (default: results)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print result without saving",
    )
    
    args = parser.parse_args()
    project_root = get_project_root()
    
    # Load config
    config = None
    if args.config:
        config_path = Path(args.config)
        if not config_path.is_absolute():
            config_path = project_root / config_path
        
        if config_path.exists():
            with open(config_path) as f:
                if config_path.suffix in [".yaml", ".yml"]:
                    config = yaml.safe_load(f)
                else:
                    config = json.load(f)
    
    # Load metrics
    metrics = None
    if args.metrics:
        if args.metrics.startswith("{"):
            metrics = json.loads(args.metrics)
        else:
            metrics_path = Path(args.metrics)
            if not metrics_path.is_absolute():
                metrics_path = project_root / metrics_path
            if metrics_path.exists():
                with open(metrics_path) as f:
                    metrics = json.load(f)
    
    # Save result
    result = save_experiment_result(
        experiment_name=args.name,
        status=args.status,
        config=config,
        metrics=metrics,
        baseline_experiment=args.baseline,
        notes=args.notes,
        output_dir=args.output_dir,
        dry_run=args.dry_run,
    )
    
    print(json.dumps(result, indent=2))
    
    if result["status"] == "error":
        sys.exit(1)


if __name__ == "__main__":
    main()

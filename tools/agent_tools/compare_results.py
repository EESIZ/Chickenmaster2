#!/usr/bin/env python3
"""Experiment Results Comparison Tool

Compares two experiment results and generates a detailed diff.
Helps identify what changed between experiments and their impact.

Usage:
    uv run python -m tools.agent_tools.compare_results --baseline results/exp_a.json --target results/exp_b.json
    uv run python -m tools.agent_tools.compare_results --baseline results/exp_a.json --target results/exp_b.json --metrics-only
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


def get_project_root() -> Path:
    """Return project root directory."""
    return Path(__file__).parent.parent.parent


def load_result(path: Path) -> dict[str, Any] | None:
    """Load experiment result JSON."""
    if not path.exists():
        return None
    try:
        with open(path) as f:
            return json.load(f)
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


def compute_diff(
    baseline: dict[str, Any],
    target: dict[str, Any],
) -> dict[str, Any]:
    """Compute differences between two flattened dictionaries."""
    diff: dict[str, Any] = {
        "added": {},
        "removed": {},
        "changed": {},
    }
    
    baseline_keys = set(baseline.keys())
    target_keys = set(target.keys())
    
    # Added keys
    for key in target_keys - baseline_keys:
        diff["added"][key] = target[key]
    
    # Removed keys
    for key in baseline_keys - target_keys:
        diff["removed"][key] = baseline[key]
    
    # Changed keys
    for key in baseline_keys & target_keys:
        if baseline[key] != target[key]:
            diff["changed"][key] = {
                "from": baseline[key],
                "to": target[key],
            }
            
            # Calculate numeric change if applicable
            if isinstance(baseline[key], (int, float)) and isinstance(target[key], (int, float)):
                change = target[key] - baseline[key]
                if baseline[key] != 0:
                    pct_change = (change / abs(baseline[key])) * 100
                    diff["changed"][key]["change"] = change
                    diff["changed"][key]["percent_change"] = round(pct_change, 2)
    
    return diff


def compare_metrics(
    baseline_metrics: dict[str, Any],
    target_metrics: dict[str, Any],
) -> dict[str, Any]:
    """Compare metrics between two experiments."""
    flat_baseline = flatten_dict(baseline_metrics)
    flat_target = flatten_dict(target_metrics)
    
    comparison: dict[str, Any] = {}
    
    all_keys = set(flat_baseline.keys()) | set(flat_target.keys())
    
    for key in sorted(all_keys):
        baseline_val = flat_baseline.get(key)
        target_val = flat_target.get(key)
        
        entry: dict[str, Any] = {
            "baseline": baseline_val,
            "target": target_val,
        }
        
        if baseline_val is not None and target_val is not None:
            if isinstance(baseline_val, (int, float)) and isinstance(target_val, (int, float)):
                change = target_val - baseline_val
                entry["change"] = change
                if baseline_val != 0:
                    entry["percent_change"] = round((change / abs(baseline_val)) * 100, 2)
                
                # Determine if improvement (assumes lower is better for loss, higher for others)
                if "loss" in key.lower() or "error" in key.lower():
                    entry["improved"] = change < 0
                else:
                    entry["improved"] = change > 0
        
        comparison[key] = entry
    
    return comparison


def compare_results(
    baseline_path: Path,
    target_path: Path,
    metrics_only: bool = False,
) -> dict[str, Any]:
    """Compare two experiment results.
    
    Args:
        baseline_path: Path to baseline result JSON
        target_path: Path to target result JSON
        metrics_only: If True, only compare metrics
        
    Returns:
        Comparison result
    """
    baseline = load_result(baseline_path)
    target = load_result(target_path)
    
    if baseline is None:
        return {
            "status": "error",
            "error_type": "FileNotFoundError",
            "message": f"Baseline file not found: {baseline_path}",
            "timestamp": datetime.now().isoformat(),
        }
    
    if target is None:
        return {
            "status": "error",
            "error_type": "FileNotFoundError",
            "message": f"Target file not found: {target_path}",
            "timestamp": datetime.now().isoformat(),
        }
    
    result: dict[str, Any] = {
        "status": "success",
        "baseline": {
            "path": str(baseline_path),
            "experiment_name": baseline.get("experiment_name"),
            "timestamp": baseline.get("timestamp"),
            "status": baseline.get("status"),
        },
        "target": {
            "path": str(target_path),
            "experiment_name": target.get("experiment_name"),
            "timestamp": target.get("timestamp"),
            "status": target.get("status"),
        },
        "timestamp": datetime.now().isoformat(),
    }
    
    # Compare metrics
    baseline_metrics = baseline.get("metrics", {})
    target_metrics = target.get("metrics", {})
    
    if baseline_metrics or target_metrics:
        result["metrics_comparison"] = compare_metrics(baseline_metrics, target_metrics)
        
        # Summary
        improved = sum(1 for v in result["metrics_comparison"].values() if v.get("improved") is True)
        degraded = sum(1 for v in result["metrics_comparison"].values() if v.get("improved") is False)
        result["metrics_summary"] = {
            "improved_count": improved,
            "degraded_count": degraded,
            "unchanged_count": len(result["metrics_comparison"]) - improved - degraded,
        }
    
    if not metrics_only:
        # Compare configs
        baseline_config = baseline.get("config", {})
        target_config = target.get("config", {})
        
        if baseline_config or target_config:
            flat_baseline = flatten_dict(baseline_config)
            flat_target = flatten_dict(target_config)
            result["config_diff"] = compute_diff(flat_baseline, flat_target)
            
            # Summary
            result["config_summary"] = {
                "added_count": len(result["config_diff"]["added"]),
                "removed_count": len(result["config_diff"]["removed"]),
                "changed_count": len(result["config_diff"]["changed"]),
            }
        
        # Compare environments
        baseline_env = baseline.get("environment", {})
        target_env = target.get("environment", {})
        
        if baseline_env or target_env:
            flat_baseline_env = flatten_dict(baseline_env)
            flat_target_env = flatten_dict(target_env)
            env_diff = compute_diff(flat_baseline_env, flat_target_env)
            
            # Only include if there are differences
            if env_diff["added"] or env_diff["removed"] or env_diff["changed"]:
                result["environment_diff"] = env_diff
    
    # Overall conclusion
    if result.get("metrics_summary"):
        summary = result["metrics_summary"]
        if summary["improved_count"] > summary["degraded_count"]:
            result["conclusion"] = "Target experiment shows overall improvement"
        elif summary["degraded_count"] > summary["improved_count"]:
            result["conclusion"] = "Target experiment shows overall degradation"
        else:
            result["conclusion"] = "Mixed results - manual review recommended"
    
    return result


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Compare experiment results (JSON output)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--baseline",
        type=str,
        required=True,
        help="Baseline experiment result file path",
    )
    parser.add_argument(
        "--target",
        type=str,
        required=True,
        help="Target experiment result file path",
    )
    parser.add_argument(
        "--metrics-only",
        action="store_true",
        help="Only compare metrics",
    )
    
    args = parser.parse_args()
    project_root = get_project_root()
    
    baseline_path = Path(args.baseline)
    if not baseline_path.is_absolute():
        baseline_path = project_root / baseline_path
    
    target_path = Path(args.target)
    if not target_path.is_absolute():
        target_path = project_root / target_path
    
    result = compare_results(
        baseline_path=baseline_path,
        target_path=target_path,
        metrics_only=args.metrics_only,
    )
    
    print(json.dumps(result, indent=2))
    
    if result["status"] == "error":
        sys.exit(1)


if __name__ == "__main__":
    main()

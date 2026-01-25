#!/usr/bin/env python3
"""Configuration Validation Tool

Validates experiment configuration files before submission.
Checks for required fields, valid values, and consistency.

Usage:
    uv run python -m tools.agent_tools.validate_config --config configs/generated/exp.yaml
    uv run python -m tools.agent_tools.validate_config --config configs/generated/exp.yaml --strict
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml


def get_project_root() -> Path:
    """Return project root directory."""
    return Path(__file__).parent.parent.parent


def load_config(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    """Load configuration file (YAML or JSON)."""
    if not path.exists():
        return None, f"Config file not found: {path}"
    
    try:
        with open(path) as f:
            if path.suffix in [".yaml", ".yml"]:
                config = yaml.safe_load(f)
            else:
                config = json.load(f)
        return config, None
    except yaml.YAMLError as e:
        return None, f"YAML parse error: {e}"
    except json.JSONDecodeError as e:
        return None, f"JSON parse error: {e}"
    except OSError as e:
        return None, f"File read error: {e}"


def load_default_config() -> dict[str, Any]:
    """Load default configuration for reference."""
    default_path = get_project_root() / "configs" / "default.yaml"
    if default_path.exists():
        config, _ = load_config(default_path)
        return config or {}
    return {}


def validate_required_fields(
    config: dict[str, Any],
    required: list[str],
) -> list[str]:
    """Validate required fields are present."""
    errors = []
    
    def get_nested(d: dict[str, Any], key_path: str) -> Any:
        keys = key_path.split(".")
        value = d
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None
        return value
    
    for field in required:
        if get_nested(config, field) is None:
            errors.append(f"Missing required field: {field}")
    
    return errors


def validate_types(
    config: dict[str, Any],
    type_specs: dict[str, type | tuple[type, ...]],
) -> list[str]:
    """Validate field types."""
    errors = []
    
    def get_nested(d: dict[str, Any], key_path: str) -> Any:
        keys = key_path.split(".")
        value = d
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None
        return value
    
    for field, expected_type in type_specs.items():
        value = get_nested(config, field)
        if value is not None and not isinstance(value, expected_type):
            errors.append(
                f"Invalid type for {field}: expected {expected_type.__name__ if isinstance(expected_type, type) else expected_type}, "
                f"got {type(value).__name__}"
            )
    
    return errors


def validate_ranges(
    config: dict[str, Any],
    range_specs: dict[str, tuple[float | None, float | None]],
) -> list[str]:
    """Validate numeric values are within ranges."""
    errors = []
    
    def get_nested(d: dict[str, Any], key_path: str) -> Any:
        keys = key_path.split(".")
        value = d
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None
        return value
    
    for field, (min_val, max_val) in range_specs.items():
        value = get_nested(config, field)
        if value is not None and isinstance(value, (int, float)):
            if min_val is not None and value < min_val:
                errors.append(f"{field} ({value}) is below minimum ({min_val})")
            if max_val is not None and value > max_val:
                errors.append(f"{field} ({value}) is above maximum ({max_val})")
    
    return errors


def validate_choices(
    config: dict[str, Any],
    choice_specs: dict[str, list[Any]],
) -> list[str]:
    """Validate field values are from allowed choices."""
    errors = []
    
    def get_nested(d: dict[str, Any], key_path: str) -> Any:
        keys = key_path.split(".")
        value = d
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None
        return value
    
    for field, choices in choice_specs.items():
        value = get_nested(config, field)
        if value is not None and value not in choices:
            errors.append(f"Invalid value for {field}: {value} (allowed: {choices})")
    
    return errors


def validate_paths(config: dict[str, Any], path_fields: list[str]) -> list[str]:
    """Validate path fields point to existing files/directories."""
    warnings = []
    project_root = get_project_root()
    
    def get_nested(d: dict[str, Any], key_path: str) -> Any:
        keys = key_path.split(".")
        value = d
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None
        return value
    
    for field in path_fields:
        value = get_nested(config, field)
        if value is not None and isinstance(value, str):
            path = Path(value)
            if not path.is_absolute():
                path = project_root / path
            if not path.exists():
                warnings.append(f"Path does not exist: {field} = {value}")
    
    return warnings


def validate_config(
    config_path: Path,
    strict: bool = False,
) -> dict[str, Any]:
    """Validate an experiment configuration file.
    
    Args:
        config_path: Path to config file
        strict: If True, treat warnings as errors
        
    Returns:
        Validation result
    """
    config, error = load_config(config_path)
    
    if error:
        return {
            "status": "error",
            "error_type": "ParseError",
            "message": error,
            "timestamp": datetime.now().isoformat(),
        }
    
    if config is None:
        return {
            "status": "error",
            "error_type": "EmptyConfig",
            "message": "Config file is empty",
            "timestamp": datetime.now().isoformat(),
        }
    
    errors: list[str] = []
    warnings: list[str] = []
    
    # Required fields
    required_fields = [
        "experiment.name",
    ]
    errors.extend(validate_required_fields(config, required_fields))
    
    # Type validation
    type_specs: dict[str, type | tuple[type, ...]] = {
        "experiment.name": str,
        "experiment.seed": int,
        "training.learning_rate": (int, float),
        "training.num_epochs": int,
        "training.batch_size": int,
        "data.max_length": int,
    }
    errors.extend(validate_types(config, type_specs))
    
    # Range validation
    range_specs: dict[str, tuple[float | None, float | None]] = {
        "training.learning_rate": (0, 1),
        "training.num_epochs": (1, 1000),
        "training.batch_size": (1, 1024),
        "training.warmup_steps": (0, 100000),
        "data.max_length": (1, 1000000),
    }
    errors.extend(validate_ranges(config, range_specs))
    
    # Path validation (as warnings)
    path_fields = [
        "model.pretrained_path",
        "data.train_path",
        "data.valid_path",
        "data.test_path",
    ]
    warnings.extend(validate_paths(config, path_fields))
    
    # Check for experiment name uniqueness recommendation
    exp_name = config.get("experiment", {}).get("name", "")
    if exp_name and not any(c.isdigit() for c in exp_name):
        warnings.append("Experiment name should include version/date for uniqueness")
    
    # Build result
    if strict:
        errors.extend(warnings)
        warnings = []
    
    result: dict[str, Any] = {
        "status": "valid" if not errors else "invalid",
        "config_path": str(config_path),
        "timestamp": datetime.now().isoformat(),
    }
    
    if errors:
        result["errors"] = errors
        result["error_count"] = len(errors)
    
    if warnings:
        result["warnings"] = warnings
        result["warning_count"] = len(warnings)
    
    if not errors:
        result["config_summary"] = {
            "experiment_name": config.get("experiment", {}).get("name"),
            "model": config.get("model", {}).get("name"),
            "learning_rate": config.get("training", {}).get("learning_rate"),
            "batch_size": config.get("training", {}).get("batch_size"),
            "epochs": config.get("training", {}).get("num_epochs"),
        }
    
    return result


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Validate experiment configuration (JSON output)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--config",
        type=str,
        required=True,
        help="Config file path to validate",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as errors",
    )
    
    args = parser.parse_args()
    project_root = get_project_root()
    
    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = project_root / config_path
    
    result = validate_config(config_path, strict=args.strict)
    
    print(json.dumps(result, indent=2))
    
    if result["status"] != "valid":
        sys.exit(1)


if __name__ == "__main__":
    main()

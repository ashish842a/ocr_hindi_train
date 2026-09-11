"""Configuration loading and merging utilities."""

import yaml
from pathlib import Path
from typing import Dict, Any, Optional


def load_config(config_path: str) -> Dict[str, Any]:
    """
    Load a YAML configuration file.

    Args:
        config_path: Path to the YAML config file

    Returns:
        Configuration dictionary
    """
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    return config or {}


def merge_config(base_config: Dict[str, Any], override_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Recursively merge override config into base config.

    Args:
        base_config: Base configuration dictionary
        override_config: Override configuration dictionary

    Returns:
        Merged configuration
    """
    if override_config is None:
        return base_config

    result = base_config.copy()

    for key, value in override_config.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_config(result[key], value)
        else:
            result[key] = value

    return result


def resolve_paths(config: Dict[str, Any], root_dir: Optional[Path] = None) -> Dict[str, Any]:
    """
    Resolve relative paths in config to absolute paths.

    Args:
        config: Configuration dictionary
        root_dir: Root directory for relative paths (defaults to cwd)

    Returns:
        Config with resolved paths
    """
    if root_dir is None:
        root_dir = Path.cwd()

    config = config.copy()

    # Resolve common path keys
    path_keys = ['data_root', 'out_dir', 'checkpoint_dir', 'log_dir']

    for key in path_keys:
        if key in config and config[key]:
            path = Path(config[key])
            if not path.is_absolute():
                config[key] = str(root_dir / path)

    return config

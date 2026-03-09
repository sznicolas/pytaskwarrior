"""
Module for extracting configuration from Taskwarrior config files.
Future extraction functions can be added here.
"""
import os
from typing import Dict

def extract_taskrc_config(taskrc_path: str) -> Dict[str, str]:
    """
    Extracts all configuration entries from a taskrc file into a dictionary.
    Args:
        taskrc_path: Path to the taskrc file.
    Returns:
        Dictionary of all config keys/values.
    """
    config = {}
    if not os.path.isfile(taskrc_path):
        raise FileNotFoundError(f"Config file not found: {taskrc_path}")
    with open(taskrc_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                config[key] = value
    return config

def get_sync_config(config: Dict[str, str]) -> Dict[str, str]:
    """
    Filters the config dict for sync-related entries (keys starting with 'sync.').
    Args:
        config: The full config dictionary.
    Returns:
        Dictionary of sync config keys/values.
    """
    return {k: v for k, v in config.items() if k.startswith('sync.')}

def get_contexts_config(config: Dict[str, str]) -> Dict[str, str]:
    """
    Filters the config dict for context-related entries (keys starting with 'context.').
    Args:
        config: The full config dictionary.
    Returns:
        Dictionary of context config keys/values.
    """
    return {k: v for k, v in config.items() if k.startswith('context.')}


"""Utility modules for Hindi HTR."""

from .device import get_device, get_amp_context
from .seed import set_seed
from .config import load_config, merge_config
from .logging_utils import setup_logger

__all__ = [
    "get_device",
    "get_amp_context",
    "set_seed",
    "load_config",
    "merge_config",
    "setup_logger",
]

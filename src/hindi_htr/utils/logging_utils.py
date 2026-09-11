"""Logging utilities for training and evaluation."""

import logging
import sys
from pathlib import Path
from typing import Optional


def setup_logger(
    name: str,
    log_file: Optional[str] = None,
    level: int = logging.INFO,
    format_str: Optional[str] = None
) -> logging.Logger:
    """
    Setup a logger with console and optional file output.

    Args:
        name: Logger name
        log_file: Optional path to log file
        level: Logging level
        format_str: Optional custom format string

    Returns:
        Configured logger
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.propagate = False

    # Clear any existing handlers
    logger.handlers.clear()

    # Default format
    if format_str is None:
        format_str = '[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s'

    formatter = logging.Formatter(format_str, datefmt='%Y-%m-%d %H:%M:%S')

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


class MetricLogger:
    """Simple metric logger for training/validation metrics."""

    def __init__(self, log_file: Optional[str] = None):
        """
        Initialize metric logger.

        Args:
            log_file: Optional CSV file to write metrics
        """
        self.metrics = []
        self.log_file = log_file

        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)

    def log(self, epoch: int, phase: str, metrics: dict) -> None:
        """
        Log metrics for an epoch.

        Args:
            epoch: Epoch number
            phase: Phase (train/val/test)
            metrics: Dictionary of metric values
        """
        entry = {'epoch': epoch, 'phase': phase, **metrics}
        self.metrics.append(entry)

        if self.log_file:
            # Write to CSV
            import csv
            file_exists = Path(self.log_file).exists()

            with open(self.log_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=entry.keys())
                if not file_exists:
                    writer.writeheader()
                writer.writerow(entry)

    def get_best(self, metric_name: str, mode: str = 'min') -> Optional[dict]:
        """
        Get best epoch by metric.

        Args:
            metric_name: Name of metric to optimize
            mode: 'min' or 'max'

        Returns:
            Best epoch's metrics or None
        """
        if not self.metrics:
            return None

        valid_metrics = [m for m in self.metrics if metric_name in m]
        if not valid_metrics:
            return None

        if mode == 'min':
            return min(valid_metrics, key=lambda x: x[metric_name])
        else:
            return max(valid_metrics, key=lambda x: x[metric_name])

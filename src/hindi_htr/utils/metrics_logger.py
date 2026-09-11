"""Metrics logger for tracking training progress."""

import json
import csv
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional


class MetricsLogger:
    """
    Logger for training metrics that saves to CSV and JSON formats.

    Tracks metrics like loss, accuracy, learning rate, etc. across epochs.
    """

    def __init__(self, log_dir: Path, experiment_name: str = "experiment"):
        """
        Initialize metrics logger.

        Args:
            log_dir: Directory to save log files
            experiment_name: Name of the experiment
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        self.experiment_name = experiment_name

        # Initialize log files
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # CSV log file
        self.csv_path = self.log_dir / f"{experiment_name}_metrics.csv"

        # JSON log file (for full history)
        self.json_path = self.log_dir / f"{experiment_name}_metrics.json"

        # Detailed JSON log with timestamp
        self.json_detailed_path = self.log_dir / f"{experiment_name}_metrics_{timestamp}.json"

        # Storage for all metrics
        self.metrics_history: List[Dict] = []

        # CSV header written flag
        self.csv_header_written = False

        # Load existing metrics if resuming
        self._load_existing_metrics()

    def _load_existing_metrics(self):
        """Load existing metrics from JSON file if it exists."""
        if self.json_path.exists():
            try:
                with open(self.json_path, 'r') as f:
                    data = json.load(f)
                    self.metrics_history = data.get('metrics', [])
                    print(f"Loaded {len(self.metrics_history)} existing metric entries")
            except Exception as e:
                print(f"Warning: Could not load existing metrics: {e}")

    def log_epoch(self, epoch: int, metrics: Dict):
        """
        Log metrics for an epoch.

        Args:
            epoch: Epoch number
            metrics: Dictionary of metrics (e.g., {'train_loss': 0.5, 'val_loss': 0.3})
        """
        # Add timestamp and epoch
        entry = {
            'epoch': epoch,
            'timestamp': datetime.now().isoformat(),
            **metrics
        }

        # Add to history
        self.metrics_history.append(entry)

        # Save to CSV (append mode)
        self._save_to_csv(entry)

        # Save to JSON (overwrite with full history)
        self._save_to_json()

    def _save_to_csv(self, entry: Dict):
        """Save a single entry to CSV file."""
        # Determine all possible fields
        fieldnames = ['epoch', 'timestamp'] + sorted([k for k in entry.keys() if k not in ['epoch', 'timestamp']])

        # Check if file exists and has content
        file_exists = self.csv_path.exists() and self.csv_path.stat().st_size > 0

        with open(self.csv_path, 'a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)

            # Write header only once
            if not file_exists:
                writer.writeheader()

            writer.writerow(entry)

    def _save_to_json(self):
        """Save full metrics history to JSON files."""
        data = {
            'experiment_name': self.experiment_name,
            'last_updated': datetime.now().isoformat(),
            'total_epochs': len(self.metrics_history),
            'metrics': self.metrics_history
        }

        # Save to main JSON file (gets overwritten each time)
        with open(self.json_path, 'w') as f:
            json.dump(data, f, indent=2)

        # Save to detailed JSON file with timestamp (archive)
        with open(self.json_detailed_path, 'w') as f:
            json.dump(data, f, indent=2)

    def get_best_epoch(self, metric: str = 'val_loss', mode: str = 'min') -> Optional[Dict]:
        """
        Get the epoch with the best metric value.

        Args:
            metric: Metric name to compare
            mode: 'min' for lowest value, 'max' for highest value

        Returns:
            Dictionary with best epoch metrics, or None if not found
        """
        if not self.metrics_history:
            return None

        # Filter entries that have the metric
        entries_with_metric = [e for e in self.metrics_history if metric in e]

        if not entries_with_metric:
            return None

        if mode == 'min':
            best_entry = min(entries_with_metric, key=lambda x: x[metric])
        else:
            best_entry = max(entries_with_metric, key=lambda x: x[metric])

        return best_entry

    def get_summary(self) -> Dict:
        """
        Get summary statistics of the training.

        Returns:
            Dictionary with summary statistics
        """
        if not self.metrics_history:
            return {}

        summary = {
            'total_epochs': len(self.metrics_history),
            'first_epoch': self.metrics_history[0]['epoch'] if self.metrics_history else None,
            'last_epoch': self.metrics_history[-1]['epoch'] if self.metrics_history else None,
        }

        # Find all metric keys (excluding epoch and timestamp)
        metric_keys = set()
        for entry in self.metrics_history:
            metric_keys.update([k for k in entry.keys() if k not in ['epoch', 'timestamp']])

        # Add best values for each metric
        for metric in metric_keys:
            if 'loss' in metric.lower() or 'error' in metric.lower():
                mode = 'min'
            else:
                mode = 'max'

            best = self.get_best_epoch(metric, mode)
            if best:
                summary[f'best_{metric}'] = best[metric]
                summary[f'best_{metric}_epoch'] = best['epoch']

        return summary

    def print_summary(self):
        """Print training summary to console."""
        summary = self.get_summary()

        print("\n" + "=" * 80)
        print("TRAINING SUMMARY")
        print("=" * 80)

        if not summary:
            print("No metrics logged yet")
            return

        print(f"Total Epochs: {summary.get('total_epochs', 'N/A')}")
        print(f"Epoch Range: {summary.get('first_epoch', 'N/A')} - {summary.get('last_epoch', 'N/A')}")
        print()

        # Print best metrics
        print("Best Metrics:")
        for key, value in sorted(summary.items()):
            if key.startswith('best_') and not key.endswith('_epoch'):
                epoch = summary.get(f'{key}_epoch', 'N/A')
                metric_name = key.replace('best_', '')
                print(f"  {metric_name}: {value:.6f} (epoch {epoch})")

        print("=" * 80)
        print(f"\nMetrics saved to:")
        print(f"  CSV:  {self.csv_path}")
        print(f"  JSON: {self.json_path}")
        print("=" * 80 + "\n")

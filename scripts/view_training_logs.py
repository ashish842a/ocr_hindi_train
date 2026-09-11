#!/usr/bin/env python3
"""
View and analyze training metrics logs.

This script helps you visualize training progress from the logged metrics.
"""

import argparse
import json
import csv
from pathlib import Path
from typing import List, Dict
import sys


def load_metrics_from_json(json_path: Path) -> List[Dict]:
    """Load metrics from JSON file."""
    with open(json_path, 'r') as f:
        data = json.load(f)
    return data.get('metrics', [])


def load_metrics_from_csv(csv_path: Path) -> List[Dict]:
    """Load metrics from CSV file."""
    metrics = []
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert numeric fields
            parsed_row = {'epoch': int(row['epoch'])}
            for key, value in row.items():
                if key == 'epoch' or key == 'timestamp':
                    continue
                try:
                    parsed_row[key] = float(value)
                except (ValueError, TypeError):
                    parsed_row[key] = value
            metrics.append(parsed_row)
    return metrics


def print_table(metrics: List[Dict], max_rows: int = None):
    """Print metrics as a formatted table."""
    if not metrics:
        print("No metrics found")
        return

    # Determine columns
    all_keys = set()
    for m in metrics:
        all_keys.update(m.keys())

    # Order columns
    ordered_keys = ['epoch']
    priority_keys = ['train_loss', 'val_loss', 'learning_rate', 'epoch_time_seconds', 'total_time_hours', 'is_best']

    for key in priority_keys:
        if key in all_keys:
            ordered_keys.append(key)
            all_keys.remove(key)

    # Add remaining keys
    ordered_keys.extend(sorted(all_keys - {'timestamp'}))

    # Print header
    header_format = " | ".join(f"{key:>15}" for key in ordered_keys)
    print(header_format)
    print("-" * len(header_format))

    # Print rows
    display_metrics = metrics[-max_rows:] if max_rows else metrics

    for m in display_metrics:
        row_values = []
        for key in ordered_keys:
            value = m.get(key, '')

            if key == 'epoch':
                row_values.append(f"{value:>15}")
            elif isinstance(value, float):
                if 'time' in key or 'lr' in key or 'learning_rate' in key:
                    row_values.append(f"{value:>15.6f}")
                else:
                    row_values.append(f"{value:>15.6f}")
            else:
                row_values.append(f"{str(value):>15}")

        print(" | ".join(row_values))


def print_summary(metrics: List[Dict]):
    """Print summary statistics."""
    if not metrics:
        print("No metrics to summarize")
        return

    print("\n" + "=" * 80)
    print("TRAINING SUMMARY")
    print("=" * 80)

    print(f"Total Epochs: {len(metrics)}")
    print(f"Epoch Range: {metrics[0]['epoch']} - {metrics[-1]['epoch']}")

    # Find best metrics
    if 'train_loss' in metrics[0]:
        train_losses = [m['train_loss'] for m in metrics]
        best_train_idx = train_losses.index(min(train_losses))
        print(f"\nBest Train Loss: {train_losses[best_train_idx]:.6f} (epoch {metrics[best_train_idx]['epoch']})")

    if 'val_loss' in metrics[0]:
        val_losses = [m['val_loss'] for m in metrics if 'val_loss' in m]
        if val_losses:
            best_val_idx = val_losses.index(min(val_losses))
            val_metrics_with_loss = [m for m in metrics if 'val_loss' in m]
            print(f"Best Val Loss: {val_losses[best_val_idx]:.6f} (epoch {val_metrics_with_loss[best_val_idx]['epoch']})")

    # Training time
    if 'total_time_hours' in metrics[-1]:
        print(f"\nTotal Training Time: {metrics[-1]['total_time_hours']:.2f} hours")

    if 'epoch_time_seconds' in metrics[0]:
        avg_epoch_time = sum(m.get('epoch_time_seconds', 0) for m in metrics) / len(metrics)
        print(f"Average Epoch Time: {avg_epoch_time:.1f} seconds")

    # Learning rate
    if 'learning_rate' in metrics[0]:
        print(f"\nInitial LR: {metrics[0]['learning_rate']:.6f}")
        print(f"Final LR: {metrics[-1]['learning_rate']:.6f}")

    print("=" * 80 + "\n")


def plot_metrics(metrics: List[Dict], metric_names: List[str]):
    """Plot metrics using matplotlib if available."""
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib not installed, cannot plot")
        print("Install with: pip install matplotlib")
        return

    epochs = [m['epoch'] for m in metrics]

    fig, axes = plt.subplots(len(metric_names), 1, figsize=(10, 4 * len(metric_names)))

    if len(metric_names) == 1:
        axes = [axes]

    for ax, metric_name in zip(axes, metric_names):
        values = [m.get(metric_name, None) for m in metrics]
        # Filter out None values
        filtered_epochs = [e for e, v in zip(epochs, values) if v is not None]
        filtered_values = [v for v in values if v is not None]

        if filtered_values:
            ax.plot(filtered_epochs, filtered_values, marker='o', linewidth=2, markersize=4)
            ax.set_xlabel('Epoch')
            ax.set_ylabel(metric_name)
            ax.set_title(f'{metric_name} vs Epoch')
            ax.grid(True, alpha=0.3)

            # Highlight best value
            if 'loss' in metric_name.lower():
                best_idx = filtered_values.index(min(filtered_values))
                best_epoch = filtered_epochs[best_idx]
                best_value = filtered_values[best_idx]
                ax.axvline(best_epoch, color='red', linestyle='--', alpha=0.5, label=f'Best: {best_value:.6f}')
                ax.legend()

    plt.tight_layout()
    plt.show()


def main():
    parser = argparse.ArgumentParser(description='View training metrics')
    parser.add_argument('--log-dir', type=str, default='logs/a1_baseline',
                        help='Directory containing log files')
    parser.add_argument('--experiment', type=str, default='a1_baseline',
                        help='Experiment name')
    parser.add_argument('--format', type=str, choices=['csv', 'json'], default='json',
                        help='Log format to read')
    parser.add_argument('--show-last', type=int, default=None,
                        help='Show only last N epochs in table')
    parser.add_argument('--plot', nargs='+', default=None,
                        help='Metrics to plot (e.g., --plot train_loss val_loss)')
    parser.add_argument('--summary-only', action='store_true',
                        help='Only show summary, not full table')

    args = parser.parse_args()

    log_dir = Path(args.log_dir)

    # Load metrics
    if args.format == 'json':
        log_file = log_dir / f"{args.experiment}_metrics.json"
        if not log_file.exists():
            print(f"Error: Log file not found: {log_file}")
            sys.exit(1)
        metrics = load_metrics_from_json(log_file)
    else:
        log_file = log_dir / f"{args.experiment}_metrics.csv"
        if not log_file.exists():
            print(f"Error: Log file not found: {log_file}")
            sys.exit(1)
        metrics = load_metrics_from_csv(log_file)

    if not metrics:
        print("No metrics found in log file")
        sys.exit(1)

    print(f"\nLoaded {len(metrics)} epochs from: {log_file}\n")

    # Show summary
    print_summary(metrics)

    # Show table
    if not args.summary_only:
        print("\nDetailed Metrics:")
        print_table(metrics, max_rows=args.show_last)

    # Plot if requested
    if args.plot:
        plot_metrics(metrics, args.plot)


if __name__ == '__main__':
    main()

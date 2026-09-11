# Training Logs Guide

The training system now automatically logs detailed metrics for every epoch in both **CSV** and **JSON** formats.

## What Gets Logged

For each epoch, the following metrics are automatically tracked:

- **epoch**: Epoch number
- **train_loss**: Training loss
- **val_loss**: Validation loss
- **learning_rate**: Current learning rate
- **epoch_time_seconds**: Time taken for this epoch (seconds)
- **total_time_seconds**: Cumulative training time (seconds)
- **total_time_hours**: Cumulative training time (hours)
- **is_best**: Whether this epoch achieved the best validation loss (1 or 0)
- **timestamp**: ISO format timestamp

## Log File Locations

When you train with `configs/a1_baseline.yaml`, logs are saved to:

```
logs/a1_baseline/
├── a1_baseline_metrics.csv              # CSV format (easy to open in Excel/spreadsheet)
├── a1_baseline_metrics.json             # JSON format (latest version, gets updated)
└── a1_baseline_metrics_YYYYMMDD_HHMMSS.json  # Timestamped archive
```

## Viewing Logs

### Method 1: View in Terminal

```bash
# Show summary and last 20 epochs
python scripts/view_training_logs.py --log-dir logs/a1_baseline

# Show only summary
python scripts/view_training_logs.py --log-dir logs/a1_baseline --summary-only

# Show last 10 epochs only
python scripts/view_training_logs.py --log-dir logs/a1_baseline --show-last 10

# Plot training curves (requires matplotlib)
python scripts/view_training_logs.py --log-dir logs/a1_baseline --plot train_loss val_loss

# Plot learning rate schedule
python scripts/view_training_logs.py --log-dir logs/a1_baseline --plot learning_rate
```

### Method 2: Open CSV in Excel/LibreOffice

Simply open `logs/a1_baseline/a1_baseline_metrics.csv` in any spreadsheet software.

### Method 3: Read JSON Programmatically

```python
import json

with open('logs/a1_baseline/a1_baseline_metrics.json', 'r') as f:
    data = json.load(f)

metrics = data['metrics']

for epoch_data in metrics:
    print(f"Epoch {epoch_data['epoch']}: "
          f"Train Loss = {epoch_data['train_loss']:.4f}, "
          f"Val Loss = {epoch_data['val_loss']:.4f}")
```

## Example Output

After training for 5 epochs, you'll see:

```
TRAINING SUMMARY
================================================================================
Total Epochs: 5
Epoch Range: 1 - 5

Best Train Loss: 1.234567 (epoch 5)
Best Val Loss: 1.345678 (epoch 4)

Total Training Time: 2.35 hours
Average Epoch Time: 1692.5 seconds

Initial LR: 0.000100
Final LR: 0.000100
================================================================================

Detailed Metrics:
          epoch |     train_loss |       val_loss |  learning_rate | epoch_time_seconds | total_time_hours |        is_best
----------------------------------------------------------------------------------------------------------------------------------------------------------
              1 |       2.345678 |       2.456789 |       0.000100 |         1650.234567 |         0.458398 |              0
              2 |       1.876543 |       1.987654 |       0.000100 |         1678.345678 |         0.924601 |              1
              3 |       1.654321 |       1.765432 |       0.000100 |         1695.456789 |         1.395437 |              1
              4 |       1.456789 |       1.345678 |       0.000100 |         1702.567890 |         1.868330 |              1
              5 |       1.234567 |       1.398765 |       0.000100 |         1715.678901 |         2.344908 |              0
```

## Auto-Resume Support

When you resume training from a checkpoint, the metrics logger will:

1. Load existing metrics from the JSON file
2. Continue logging from the last epoch
3. Maintain the complete training history

This means your logs are preserved even if training is interrupted!

## Integration with Configs

The logging is configured in your YAML config file:

```yaml
training:
  checkpoint_dir: checkpoints/a1_baseline
  log_dir: logs/a1_baseline              # Directory for log files
  experiment_name: a1_baseline           # Experiment name (used in filenames)
```

## Tips

1. **Monitor during training**: Use `tail -f` to watch the CSV file update in real-time:
   ```bash
   tail -f logs/a1_baseline/a1_baseline_metrics.csv
   ```

2. **Compare experiments**: Each experiment saves its own logs, so you can easily compare:
   ```bash
   python scripts/view_training_logs.py --log-dir logs/a1_baseline --summary-only
   python scripts/view_training_logs.py --log-dir logs/a2_augmentation --summary-only
   ```

3. **Plot with external tools**: The CSV format is compatible with any plotting tool (Excel, Google Sheets, Python pandas, R, etc.)

4. **Archive logs**: The timestamped JSON files provide permanent snapshots of your training runs

## Troubleshooting

**Q: I don't see any log files**
- A: Make sure you've started training. Logs are created on the first epoch.

**Q: Logs stopped updating**
- A: Check if training is still running. Logs are written at the end of each epoch.

**Q: Can I add custom metrics?**
- A: Yes! Modify `src/hindi_htr/engine/trainer.py` in the `train()` method where `log_metrics` is defined.

**Q: How do I plot training curves?**
- A: Install matplotlib: `pip install matplotlib`
  Then use: `python scripts/view_training_logs.py --plot train_loss val_loss`

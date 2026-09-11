# Terminal Logs Guide

All terminal output (including progress bars, warnings, and errors) can now be saved to log files for documentation and debugging.

## Training with Terminal Logs

Instead of:
```bash
python scripts/train.py --config configs/a1_baseline.yaml
```

Use:
```bash
./scripts/train_with_log.sh configs/a1_baseline.yaml
```

This will:
- Display output in terminal (live)
- Save ALL output to `logs/a1_baseline_terminal_YYYYMMDD_HHMMSS.log`
- Include progress bars, warnings, errors, and all printed messages

## Evaluation with Terminal Logs

Instead of:
```bash
python scripts/evaluate.py --config configs/a1_baseline.yaml --checkpoint checkpoints/a1_baseline/best.pt --split test --output results/test.json
```

Use:
```bash
./scripts/evaluate_with_log.sh \
    --config configs/a1_baseline.yaml \
    --checkpoint checkpoints/a1_baseline/best.pt \
    --split test \
    --output results/test.json
```

This saves output to `logs/a1_baseline_eval_test_YYYYMMDD_HHMMSS.log`

## What Gets Saved

Terminal log files capture:
- ✅ All INFO/WARNING/ERROR messages
- ✅ Training progress bars (epoch progress, batch progress)
- ✅ Epoch metrics (train loss, val loss, learning rate)
- ✅ Timing information
- ✅ Model architecture details
- ✅ FutureWarnings and deprecation notices
- ✅ Stack traces if errors occur
- ✅ Evaluation results and confidence intervals

## Log File Locations

```
logs/
├── a1_baseline/                           # Structured metrics (CSV/JSON)
│   ├── a1_baseline_metrics.csv
│   └── a1_baseline_metrics.json
├── a1_baseline_terminal_20260910_163045.log  # Training terminal output
└── a1_baseline_eval_test_20260910_170023.log # Evaluation terminal output
```

## Viewing Terminal Logs

```bash
# View full log
cat logs/a1_baseline_terminal_20260910_163045.log

# View last 50 lines
tail -50 logs/a1_baseline_terminal_20260910_163045.log

# Search for errors
grep -i error logs/a1_baseline_terminal_20260910_163045.log

# Search for warnings
grep -i warning logs/a1_baseline_terminal_20260910_163045.log

# View with less (scrollable)
less logs/a1_baseline_terminal_20260910_163045.log
```

## Archiving Terminal Logs

Terminal logs are automatically archived when you run:
```bash
./experiments/archive_experiment.sh v2_charset100 "Description"
```

They will be saved to:
```
experiments/archive/v2_charset100_*/terminal_logs/
```

## Example: Complete Training Workflow with Logs

```bash
# 1. Train with terminal logging
./scripts/train_with_log.sh configs/a1_baseline.yaml

# Output:
# Starting training with config: configs/a1_baseline.yaml
# Terminal output will be saved to: logs/a1_baseline_terminal_20260910_163045.log
# [All training output displayed and saved]

# 2. Evaluate with terminal logging
./scripts/evaluate_with_log.sh \
    --config configs/a1_baseline.yaml \
    --checkpoint checkpoints/a1_baseline/best.pt \
    --split test \
    --output results/a1_test.json

# Output:
# Starting evaluation with:
#   Config: configs/a1_baseline.yaml
#   Checkpoint: checkpoints/a1_baseline/best.pt
#   Split: test
# Terminal output will be saved to: logs/a1_baseline_eval_test_20260910_170023.log
# [All evaluation output displayed and saved]

# 3. Archive everything (includes terminal logs)
./experiments/archive_experiment.sh v2_charset100 "Baseline with 100 chars"

# 4. View archived terminal logs
cat experiments/archive/v2_charset100_*/terminal_logs/*.log
```

## Benefits for Paper Documentation

Terminal logs are useful for:

1. **Debugging**: Full stack traces and error messages saved
2. **Reproducibility**: Exact output can be verified
3. **Paper Appendix**: Include training curves and metrics
4. **Progress Tracking**: See how long each epoch took
5. **Warnings**: Document any deprecation warnings or issues
6. **Comparison**: Compare terminal output across experiments

## Tips

1. **Always use the wrapper scripts** for experiments you want to document
2. **Keep terminal logs** for successful runs (archive them)
3. **Check logs after failures** to debug issues
4. **Include in appendix** when submitting papers
5. **Clean old logs** after archiving to save space

## File Size

Terminal logs are typically:
- Training: 100-500 KB for 50 epochs
- Evaluation: 10-50 KB per split

Small enough to keep for all experiments!

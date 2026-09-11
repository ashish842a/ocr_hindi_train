# Checkpoint Management Guide

## Checkpoint Saving Strategy

The trainer automatically saves three types of checkpoints:

### 1. **latest.pt** (Auto-Resume)
- Saved: **Every epoch**
- Purpose: Automatic resume after interruption
- Location: `checkpoints/<experiment_name>/latest.pt`
- Always overwritten with the most recent epoch

### 2. **best.pt** (Best Model)
- Saved: When validation loss improves
- Purpose: Best model for final evaluation
- Location: `checkpoints/<experiment_name>/best.pt`
- Keeps the model with lowest validation loss

### 3. **epoch_XXX.pt** (Periodic Snapshots)
- Saved: Every N epochs (default: 5)
- Purpose: Multiple checkpoints for analysis
- Location: `checkpoints/<experiment_name>/epoch_005.pt`, `epoch_010.pt`, etc.
- Configurable via `save_checkpoint_every` in config

## Checkpoint Contents

Each checkpoint file contains:
```python
{
    'epoch': 42,                      # Current epoch number
    'model_state_dict': {...},        # Model weights
    'optimizer_state_dict': {...},    # Optimizer state
    'scaler_state_dict': {...},       # AMP scaler state (if using AMP)
    'metrics': {
        'loss': 0.234,
        'val_loss': 0.189,
        ...
    },
    'config': {...}                   # Full training config
}
```

## Usage Examples

### Example 1: Normal Training (Auto-Resume)

```bash
# Start training
python scripts/train.py --config configs/a1_baseline.yaml

# If interrupted (Ctrl+C, OOM, timeout), just run again:
python scripts/train.py --config configs/a1_baseline.yaml
# ✅ Automatically resumes from latest.pt
```

**Console output:**
```
[INFO] Found existing checkpoint: checkpoints/a1_baseline/latest.pt
[INFO] Resuming from latest checkpoint (use --no-resume to start fresh)
[INFO] Loaded checkpoint from epoch 23
[INFO] Best val loss so far: 0.1890 at epoch 21
[INFO] Starting training for 50 epochs (from epoch 24)
```

### Example 2: Force Fresh Training

```bash
# Ignore existing checkpoints and start from scratch
python scripts/train.py --config configs/a1_baseline.yaml --no-resume
```

**Console output:**
```
[INFO] --no-resume flag set, starting fresh training
[INFO] Starting training for 50 epochs (from epoch 1)
```

### Example 3: Resume from Specific Epoch

```bash
# Resume from epoch 30
python scripts/train.py \
    --config configs/a1_baseline.yaml \
    --resume checkpoints/a1_baseline/epoch_030.pt
```

**Console output:**
```
[INFO] Resuming from checkpoint: checkpoints/a1_baseline/epoch_030.pt
[INFO] Loaded checkpoint from epoch 30
[INFO] Starting training for 50 epochs (from epoch 31)
```

### Example 4: Resume from Best Model

```bash
# Continue training from the best checkpoint
python scripts/train.py \
    --config configs/a1_baseline.yaml \
    --resume checkpoints/a1_baseline/best.pt
```

## Configuring Checkpoint Frequency

Edit your config YAML file:

```yaml
training:
  num_epochs: 50
  save_checkpoint_every: 5  # Save epoch checkpoint every N epochs
```

**Recommendations:**

| Training Duration | `save_checkpoint_every` | Disk Usage (per checkpoint) |
|-------------------|-------------------------|------------------------------|
| Quick test (5-10 epochs) | 1 | ~500 MB |
| Short run (20 epochs) | 5 | ~500 MB |
| Full run (50 epochs) | 5 | ~500 MB |
| Long run (100 epochs) | 10 | ~500 MB |

**Note:** `latest.pt` and `best.pt` are ALWAYS saved regardless of this setting.

## Checkpoint Directory Structure

```
checkpoints/
├── a1_baseline/
│   ├── latest.pt         ← Always updated (auto-resume)
│   ├── best.pt           ← Best validation loss
│   ├── epoch_005.pt      ← Every 5 epochs
│   ├── epoch_010.pt
│   ├── epoch_015.pt
│   └── ...
├── a2_augmentation/
│   ├── latest.pt
│   ├── best.pt
│   └── ...
└── a5_joint_ctc_attention/
    ├── latest.pt
    ├── best.pt
    └── ...
```

## Common Scenarios

### Scenario 1: Colab Timeout (12-hour limit)

```bash
# Session 1: Train for 12 hours, reaches epoch 42
python scripts/train.py --config configs/a1_baseline.yaml

# Session 2: Automatically resumes from epoch 42
python scripts/train.py --config configs/a1_baseline.yaml
```

### Scenario 2: Out of Memory (OOM)

```bash
# Training crashes at epoch 15 due to OOM

# Fix: Reduce batch size in config
# training.batch_size: 32 → 16

# Resume training with smaller batch size
python scripts/train.py --config configs/a1_baseline.yaml
# ✅ Resumes from epoch 15 with new batch size
```

### Scenario 3: Experiment with Different Settings

```bash
# Train baseline for 30 epochs
python scripts/train.py --config configs/a1_baseline.yaml

# Want to try higher learning rate from epoch 30:
# 1. Edit config: optimizer.lr: 0.0001 → 0.0005
# 2. Resume from epoch_030.pt
python scripts/train.py \
    --config configs/a1_baseline.yaml \
    --resume checkpoints/a1_baseline/epoch_030.pt
```

### Scenario 4: Delete and Start Fresh

```bash
# Option A: Delete specific experiment checkpoints
rm -rf checkpoints/a1_baseline/
python scripts/train.py --config configs/a1_baseline.yaml

# Option B: Keep checkpoints but force fresh training
python scripts/train.py --config configs/a1_baseline.yaml --no-resume
```

## Checkpoint Inspection

To inspect a checkpoint without training:

```python
import torch

# Load checkpoint
checkpoint = torch.load('checkpoints/a1_baseline/best.pt', map_location='cpu')

# View info
print(f"Epoch: {checkpoint['epoch']}")
print(f"Metrics: {checkpoint['metrics']}")
print(f"Config: {checkpoint['config']}")
```

Or from command line:

```bash
python -c "
import torch
ckpt = torch.load('checkpoints/a1_baseline/best.pt', map_location='cpu')
print(f\"Epoch: {ckpt['epoch']}\")
print(f\"Val Loss: {ckpt['metrics'].get('val_loss', 'N/A')}\")
"
```

## Best Practices

1. **Always keep latest.pt** - Enables seamless auto-resume
2. **Use best.pt for evaluation** - Best model performance
3. **Keep epoch checkpoints for analysis** - Compare different training stages
4. **Regular backups** - Copy `best.pt` to safe location before long runs
5. **Disk space management** - Each checkpoint is ~500 MB for ResNet50

## FAQ

**Q: What happens if I run training and latest.pt exists?**
A: Training automatically resumes from that checkpoint.

**Q: How do I start fresh training?**
A: Use `--no-resume` flag or delete the checkpoint directory.

**Q: Can I resume training with a different config?**
A: Yes, but be careful - changes to model architecture won't work. Changes to learning rate, batch size, etc. will work.

**Q: What if best.pt is at epoch 20 but latest.pt is at epoch 25?**
A: Auto-resume starts from epoch 26 (latest), but best.pt is still saved separately for evaluation.

**Q: How much disk space do I need?**
A: For 50 epochs with `save_checkpoint_every: 5`:
- latest.pt: ~500 MB
- best.pt: ~500 MB  
- epoch_005, 010, ..., 050: 10 × 500 MB = 5 GB
- **Total: ~6 GB** per experiment

**Q: Can I change save_checkpoint_every during training?**
A: Yes, edit the config and resume. Future epochs will use the new frequency.

# Quick Start Guide - Hindi HTR Training

## Prerequisites

1. **Python 3.11 or 3.12** (PyTorch has no wheels for Python 3.14)
2. **CUDA-capable GPU** recommended (training will be very slow on CPU)
3. **IIIT-HW-Hindi dataset** in `dataset/IIIT-HW-Hindi_v1/`

## Step-by-Step Training Commands

### Step 1: Install Dependencies

```bash
# Create virtual environment (Python 3.11 or 3.12)
python3.11 -m venv venv
source venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

### Step 2: Prepare Dataset (CPU-only, ~5-10 minutes)

This dataset-preparation command is intentionally run on the CPU only. It does not need a GPU and should be executed before training. For training on a CUDA-capable GPU, use the training command from Step 3, for example:

```bash
python scripts/train.py --config configs/a1_baseline.yaml
```

```bash
python scripts/prepare_data.py \
    --data-root dataset/IIIT-HW-Hindi_v1 \
    --output-dir data_processed \
    --min-char-freq 50 \
    --normalize
```

**Output:**
- `data_processed/train_manifest.jsonl` (69,853 samples)
- `data_processed/val_manifest.jsonl` (12,708 samples)
- `data_processed/test_manifest.jsonl` (12,869 samples)
- `data_processed/charset.json` (~100 characters)
- `data_processed/statistics.json`

### Step 3: Start Training

#### Option A: Fresh Training

```bash
# A1: Corrected baseline (recommended first experiment)
python scripts/train.py --config configs/a1_baseline.yaml
```

#### Option B: Auto-Resume from Last Checkpoint

```bash
# Automatically resumes from latest checkpoint if it exists
python scripts/train.py --config configs/a1_baseline.yaml
```

#### Option C: Force Fresh Training (ignore checkpoints)

```bash
# Use --no-resume to ignore existing checkpoints
python scripts/train.py --config configs/a1_baseline.yaml --no-resume
```

#### Option D: Resume from Specific Checkpoint

```bash
# Resume from a specific checkpoint file
python scripts/train.py \
    --config configs/a1_baseline.yaml \
    --resume checkpoints/a1_baseline/epoch_025.pt
```

### Step 4: Monitor Training

Training logs and checkpoints are saved to:

```
checkpoints/a1_baseline/
├── latest.pt           # Always updated (auto-resume uses this)
├── best.pt             # Best validation loss
├── epoch_005.pt        # Saved every 5 epochs
├── epoch_010.pt
├── epoch_015.pt
└── ...

logs/a1_baseline/
└── train.log           # Training logs
```

**Checkpoint Strategy:**
- `latest.pt` - Saved **every epoch** (for auto-resume)
- `best.pt` - Saved when validation loss improves
- `epoch_XXX.pt` - Saved **every 5 epochs** (configurable)

### Step 5: Evaluate Model

```bash
# Evaluate on test set with bootstrap confidence intervals
python scripts/evaluate.py \
    --config configs/a1_baseline.yaml \
    --checkpoint checkpoints/a1_baseline/best.pt \
    --split test \
    --decode-method greedy \
    --bootstrap-ci \
    --output results/a1_test_results.json
```

**With beam search decoding:**

```bash
python scripts/evaluate.py \
    --config configs/a1_baseline.yaml \
    --checkpoint checkpoints/a1_baseline/best.pt \
    --split test \
    --decode-method beam \
    --beam-width 10 \
    --bootstrap-ci \
    --output results/a1_test_beam.json
```

## Training Different Experiments

### A0: Paper as Written (WILL FAIL - documents G1)

```bash
python scripts/train.py --config configs/a0_paper_asis.yaml
```

### A2: With Augmentation

```bash
python scripts/train.py --config configs/a2_augmentation.yaml
```

### A5: Joint CTC-Attention (Headline Model)

```bash
python scripts/train.py --config configs/a5_joint_ctc_attention.yaml
```

### P1: Quick Sanity Check (CPU-compatible)

```bash
# Small CRNN model for smoke testing
python scripts/train.py --config configs/p1_crnn_sanity.yaml
```

## Checkpoint Configuration

To change checkpoint saving frequency, edit the config file:

```yaml
training:
  save_checkpoint_every: 5  # Save epoch checkpoint every N epochs
```

**Examples:**
- `save_checkpoint_every: 1` - Save every epoch (uses more disk space)
- `save_checkpoint_every: 10` - Save every 10 epochs (uses less disk space)
- `save_checkpoint_every: 5` - Default (balanced)

## Troubleshooting

### Training Interrupted

**Solution:** Just run the same command again:

```bash
python scripts/train.py --config configs/a1_baseline.yaml
```

It will automatically resume from `latest.pt`.

### Out of Memory (OOM)

**Solution:** Reduce batch size in config:

```yaml
training:
  batch_size: 16  # Reduce from 32
  val_batch_size: 16
```

### Too Slow on CPU

**Solution:** Use the small CRNN model for testing:

```bash
python scripts/train.py --config configs/p1_crnn_sanity.yaml
```

### Want to Delete Checkpoints and Start Fresh

```bash
# Delete checkpoints for a specific experiment
rm -rf checkpoints/a1_baseline/

# Then run training again
python scripts/train.py --config configs/a1_baseline.yaml
```

## Expected Training Time

On a single GPU (e.g., NVIDIA T4 or RTX 3090):

- **A1 Baseline (ResNet50)**: ~6-8 hours for 50 epochs
- **A5 Joint CTC-Attention**: ~8-10 hours for 50 epochs
- **P1 CRNN Sanity**: ~1-2 hours for 5 epochs

On Google Colab (T4 GPU, 12-hour limit):

- Can complete ~40-45 epochs before timeout
- Use checkpoint resume to continue in next session

## Next Steps

After training A1 baseline:

1. **Evaluate on test set** to get CER/WER metrics
2. **Compare A0 vs A1** to document G1 (stride fix)
3. **Train A2** with augmentation
4. **Train A5** for joint CTC-Attention
5. **Run ablation studies** A0-A8

## Quick Reference: All Commands

```bash
# 1. Prepare data
python scripts/prepare_data.py --data-root dataset/IIIT-HW-Hindi_v1 --output-dir data_processed

# 2. Train (auto-resumes)
python scripts/train.py --config configs/a1_baseline.yaml

# 3. Evaluate
python scripts/evaluate.py --config configs/a1_baseline.yaml --checkpoint checkpoints/a1_baseline/best.pt --split test --bootstrap-ci --output results/a1_test.json

# 4. Force fresh training
python scripts/train.py --config configs/a1_baseline.yaml --no-resume

# 5. Resume from specific checkpoint
python scripts/train.py --config configs/a1_baseline.yaml --resume checkpoints/a1_baseline/epoch_025.pt
```

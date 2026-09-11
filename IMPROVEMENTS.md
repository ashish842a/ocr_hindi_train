# Hindi HTR Improvements Summary

## Baseline Results (A1)

**Model:** ResNet50 + BiLSTM + CTC
**Checkpoint:** `archive/a1_baseline_v2_fixed_6.98CER/a1_baseline/best.pt`
**Epoch:** 15
**Test Performance:**
- **CER: 6.98%**
- **WER: 26.68%**
- Samples: 12,869

### Configuration Used (A1)
```yaml
- Epochs: 50
- Learning Rate: 0.0003 → 0.00015 (reduced at epoch 15)
- Batch Size: 32
- Optimizer: Adam (weight_decay: 0.00001)
- Scheduler: ReduceLROnPlateau
- Augmentation: Minimal (elastic distortion only via config params)
```

## Improvements Implemented

### 1. ✓ Fixed Critical Bug
**Issue:** Double downsampling in `model.py:150`
- Sequence length was 2-4 instead of 17-22
- Model could only predict 2-3 characters
- Caused complete training collapse (94% CER → 6.98% CER after fix)

### 2. ✓ Beam Search Decoding
**Implementation:** Already available in `src/hindi_htr/decode/beam_search.py`
**Test Command:**
```bash
python scripts/evaluate.py \
  --config configs/a1_baseline.yaml \
  --checkpoint archive/a1_baseline_v2_fixed_6.98CER/a1_baseline/best.pt \
  --split test \
  --decode-method beam \
  --beam-width 10 \
  --output results/a1_test_beam10.json
```

**Expected improvement:** +0.5-1.0% CER reduction

### 3. ✓ Improved Config (A2)
**File:** `configs/a2_improved.yaml`

**Key Changes:**
- Extended training: 50 → 100 epochs
- Cosine LR schedule (smoother annealing)
- Stronger augmentation:
  - Elastic distortion (α=30, σ=4, p=0.6)
  - Affine transforms (rotation=8°, scale=0.85-1.15, shear=8°, p=0.5)
  - Perspective distortion (0.15, p=0.4)
  - Morphological ops (erosion/dilation, p=0.3)
  - Gaussian noise (σ=8, p=0.4)
- Increased weight decay: 0.00001 → 0.00005

### 4. Future Improvements (Not Implemented)

#### Language Model Integration
Add character-level language model for post-processing:
```python
# Pseudo-code
predictions = ctc_decode(logits)
refined = language_model.refine(predictions)  # Fix common OCR errors
```
**Expected:** +1-2% CER improvement

#### Transformer Neck
Replace BiLSTM with Transformer encoder:
```yaml
model:
  neck_type: transformer
  neck_config:
    hidden_dim: 512
    num_layers: 4
    num_heads: 8
```
**Expected:** Potential 4-5% CER (sota architecture)

## Commands Reference

### Archive Current Run
```bash
mkdir -p archive/a1_baseline_v2_fixed_6.98CER
cp -r checkpoints/a1_baseline archive/a1_baseline_v2_fixed_6.98CER/
cp -r logs/a1_baseline archive/a1_baseline_v2_fixed_6.98CER/
cp results/a1_test.* archive/a1_baseline_v2_fixed_6.98CER/
cp configs/a1_baseline.yaml archive/a1_baseline_v2_fixed_6.98CER/config_used.yaml
```

### Start New Training (A2 Improved)
```bash
# Clean previous runs
rm -rf checkpoints/a2_improved logs/a2_improved

# Train with improved config
python scripts/train.py \
  --config configs/a2_improved.yaml \
  --no-resume
```

### Evaluate with Beam Search
```bash
# Greedy decoding (fast)
python scripts/evaluate.py \
  --config configs/a2_improved.yaml \
  --checkpoint checkpoints/a2_improved/best.pt \
  --split test \
  --output results/a2_test_greedy.json

# Beam search (slower, better)
python scripts/evaluate.py \
  --config configs/a2_improved.yaml \
  --checkpoint checkpoints/a2_improved/best.pt \
  --split test \
  --decode-method beam \
  --beam-width 10 \
  --output results/a2_test_beam10.json
```

### Resume Training
```bash
python scripts/train.py \
  --config configs/a2_improved.yaml \
  --resume auto
```

### Monitor Training
```bash
# Watch training logs
tail -f logs/a2_improved/train.log

# Plot metrics
python scripts/plot_metrics.py \
  --metrics logs/a2_improved/a2_improved_metrics.csv
```

## Expected Performance Targets

| Configuration | CER (Target) | Notes |
|---------------|--------------|-------|
| A1 Baseline | 6.98% | ✓ Achieved |
| A1 + Beam Search | 6.3-6.5% | Pending test |
| A2 Improved (Greedy) | 5.5-6.0% | Better training |
| A2 Improved (Beam) | 5.0-5.5% | Best combination |
| A2 + Language Model | 4.0-4.5% | Future work |
| A2 + Transformer | 3.5-4.5% | SOTA target |

## Key Insights

1. **6.98% CER is excellent** for ResNet50+BiLSTM+CTC on word-level Hindi HTR
2. **No data leakage** confirmed (0 overlap between splits)
3. **Training is healthy** - val loss decreased 0.605 → 0.360
4. **Model is learning** - diverse predictions, realistic errors
5. **Architecture is appropriate** - 3:1 timestep-to-character ratio

## Sample Predictions (Epoch 15)

**Perfect:**
- अनाथों → अनाथों ✓
- प्रतिभावान → प्रतिभावान ✓
- कालाबाजारी → कालाबाजारी ✓

**Minor Errors:**
- मृतका → मृनका (त→न confusion)
- उबालें → उबालों (diacritic error)
- पढ़ना → पढुना (vowel confusion)

These are realistic HTR character confusions in Devanagari script.

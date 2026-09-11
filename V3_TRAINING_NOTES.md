# V3 Training - Fixed Version

**Date:** 2026-09-10
**Status:** READY TO TRAIN
**Previous:** V2 archived (CER 50.73%, WER 97.14% - BROKEN)

---

## Bugs Fixed from V2

### 1. Double Downsampling Bug (CRITICAL)
- **Was:** `(w // 4) / 8 = w / 32` → 4x sequence compression
- **Now:** `w // 8` → Correct downsampling factor
- **Impact:** Model now gets correct sequence lengths (32 frames instead of 8)

### 2. Label Padding Bug
- **Was:** Padding with `value=0` (blank token)
- **Now:** Padding with `value=-1` (ignored by CTC)
- **Impact:** Cleaner training, no confusion from blank in ground truth

---

## Changes Made

| File | Line | Change | Reason |
|------|------|--------|--------|
| `bucket_sampler.py` | 170 | `w // 4` → `w // 8` | Match ResNet downsampling |
| `bucket_sampler.py` | 162 | `value=0` → `value=-1` | Don't use blank in labels |
| `trainer.py` | 114 | Removed `/ 8` | Already correct from collate_fn |
| `trainer.py` | 205 | Removed `/ 8` | Same for validation |

---

## Expected Results

| Metric | V2 (Buggy) | V3 (Conservative) | V3 (Optimistic) |
|--------|-----------|------------------|----------------|
| **CER** | 50.73% | 10-25% | 5-15% |
| **WER** | 97.14% | 30-60% | 20-40% |

**Confidence:** 95% that V3 will be dramatically better (WER < 60%)

---

## Training Command

```bash
# Clean start
rm -rf checkpoints/a1_baseline/*
rm -rf logs/a1_baseline/*

# Train V3
python scripts/train.py --config configs/a1_baseline.yaml
```

**Config:** `configs/a1_baseline.yaml`
- Epochs: 50
- Batch size: 32
- Learning rate: 0.0001 (Adam)
- No augmentation (for now)
- Use AMP: true

---

## What to Monitor

### During Training:
1. **Train loss should decrease** (same as V2)
2. **Val loss should decrease** (same as V2)
3. **Best epoch around 30-40** (similar to V2's epoch 35)

### After Training:
1. **Evaluate on test set:**
   ```bash
   python scripts/evaluate.py \
       --config configs/a1_baseline.yaml \
       --checkpoint checkpoints/a1_baseline/best.pt \
       --split test \
       --bootstrap-ci \
       --output results/v3_test.json
   ```

2. **Expected improvement:**
   - WER should be **< 60%** (from 97%)
   - CER should be **< 30%** (from 50%)

---

## If Results Are Still Bad

If WER > 60% after V3 training, check:

1. **Sequence length mismatch?**
   ```python
   # Debug script to verify
   python -c "
   import torch
   from src.hindi_htr.models import build_model
   model = build_model({'backbone_type':'resnet50', 'neck_type':'bilstm', 'head_type':'ctc', 'num_classes':102})
   x = torch.randn(1,3,64,256)
   out = model(x)
   print(f'Input width: 256, Output seq: {out[\"ctc_logits\"].shape[1]}')
   print(f'Expected: 256/8=32, Got: {out[\"ctc_logits\"].shape[1]}')
   "
   ```

2. **Data issues?** Check a few samples manually
3. **Other bugs?** We'll debug together

---

## Post-Training Improvements (If Needed)

If V3 results are good but not great, try:

1. **Enable augmentation:**
   ```yaml
   augmentation:
     enabled: true
   ```

2. **Train longer:**
   ```yaml
   training:
     num_epochs: 100
   ```

3. **Add learning rate schedule:**
   ```yaml
   training:
     scheduler:
       type: cosine
       warmup_epochs: 5
   ```

4. **Increase model capacity:**
   ```yaml
   model:
     neck_config:
       hidden_dim: 1024  # from 512
       num_layers: 3     # from 2
   ```

---

## Archive Info

- **V2 archived at:** `archive/v2_buggy_double_downsampling/`
- **V2 size:** 5.5GB (all checkpoints + logs)
- **V2 bug report:** See `archive/v2_buggy_double_downsampling/BUG_REPORT.md`

---

## Timeline

- **V2 Training:** ~2 hours (50 epochs)
- **V2 Results:** FAILED (97% WER)
- **Bug Found:** 2026-09-10 23:00
- **Fixes Applied:** 2026-09-10 23:15
- **V2 Archived:** 2026-09-10 23:28
- **V3 Ready:** 2026-09-10 23:30

---

**STATUS:** ✅ Ready to train V3

**Command to start:**
```bash
python scripts/train.py --config configs/a1_baseline.yaml
```

**Good luck! 🚀**

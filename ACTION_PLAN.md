# Action Plan: From 6.24% to <4% CER

**Current Status (Epoch 12/100):**
- CER: 6.24%
- WER: 24.85%
- Model: A2 (ResNet50 + BiLSTM + CTC)

**Target:**
- CER: <4.0% (36% improvement)
- WER: <18% (28% improvement)


---

## ✅ Immediate Actions (Today)

### 1. **Continue A2 Training** [Already Running]
```bash
# Monitor progress
tail -f logs/a2_improved/train.log

# Check latest metrics
tail logs/a2_improved/a2_improved_metrics.csv
```

**Expected at epoch 100:** CER ~5.0%, WER ~21%

### 2. **Build Character Language Model** [10 minutes]
```bash
# Train 5-gram character LM
python scripts/train_char_lm.py \
  --n 5 \
  --train-manifest data_processed/train_manifest.jsonl \
  --output models/char_5gram_lm.pkl \
  --test

# Expected output:
# ✓ Trained on 69,853 samples
# ✓ Vocabulary: ~100 characters
# ✓ Model saved to: models/char_5gram_lm.pkl
```

**Impact:** -0.8 to -1.2% CER when integrated with beam search

### 3. **Start Joint CTC-Attention Training** [5 minutes setup]
```bash
# Start parallel training with attention
python scripts/train.py \
  --config configs/a3_joint_ctc_attention.yaml \
  --no-resume

# Monitor
tail -f logs/a3_joint_ctc_attention/train.log
```

**Expected at epoch 100:** CER ~4.0-4.5%, WER ~18-20%

---

## 🎯 This Week (Days 1-7)

### Monday: Setup & Launch
- [x] Continue A2 training (already running)
- [ ] Build character LM (10 mins)
- [ ] Start A3 joint training (5 mins)
- [ ] Test beam search on A1 (check results)

### Tuesday-Friday: Monitor Training
```bash
# Daily checks (2 mins each)
# 1. Check A2 progress
tail -5 logs/a2_improved/a2_improved_metrics.csv

# 2. Check A3 progress
tail -5 logs/a3_joint_ctc_attention/a3_joint_ctc_attention_metrics.csv

# 3. Quick evaluation at milestones
# At epoch 20, 40, 60, 80, 100
python scripts/evaluate.py \
  --config configs/a2_improved.yaml \
  --checkpoint checkpoints/a2_improved/best.pt \
  --split test \
  --output results/a2_epoch${EPOCH}.json
```

### Weekend: Evaluation & Analysis
```bash
# Compare A2 vs A3
python scripts/evaluate.py \
  --config configs/a2_improved.yaml \
  --checkpoint checkpoints/a2_improved/best.pt \
  --split test \
  --bootstrap-ci \
  --output results/a2_final.json

python scripts/evaluate.py \
  --config configs/a3_joint_ctc_attention.yaml \
  --checkpoint checkpoints/a3_joint_ctc_attention/best.pt \
  --split test \
  --bootstrap-ci \
  --output results/a3_final.json
```

---

## 📅 Week 2: Advanced Improvements

### Implement Beam Search with Language Model

**1. Create beam search + LM decoder** (2 hours)

```python
# src/hindi_htr/decode/beam_search_lm.py
def beam_search_with_lm(
    logits,
    charset,
    lm=None,
    beam_width=20,
    lm_weight=0.3
):
    """
    Beam search with language model rescoring.

    Final score = (1 - lm_weight) * ctc_score + lm_weight * lm_score
    """
    # Implementation...
    pass
```

**2. Test on best models**

```bash
# Load LM
python scripts/evaluate.py \
  --config configs/a3_joint_ctc_attention.yaml \
  --checkpoint checkpoints/a3_joint_ctc_attention/best.pt \
  --split test \
  --decode-method beam \
  --beam-width 20 \
  --lm models/char_5gram_lm.pkl \
  --lm-weight 0.3 \
  --output results/a3_beam_lm.json
```

**Expected improvement:** -0.8 to -1.2% CER

---

## 📅 Week 3: Fine-Tuning & Optimization

### 1. Test Different Beam Widths
```bash
for width in 5 10 20 50; do
  python scripts/evaluate.py \
    --config configs/a3_joint_ctc_attention.yaml \
    --checkpoint checkpoints/a3_joint_ctc_attention/best.pt \
    --split test \
    --decode-method beam \
    --beam-width $width \
    --output results/a3_beam${width}.json
done

# Find optimal beam width
python scripts/compare_beam_widths.py results/a3_beam*.json
```

### 2. Tune Language Model Weight
```bash
for lm_weight in 0.1 0.2 0.3 0.4 0.5; do
  python scripts/evaluate.py \
    --config configs/a3_joint_ctc_attention.yaml \
    --checkpoint checkpoints/a3_joint_ctc_attention/best.pt \
    --split val \
    --decode-method beam \
    --beam-width 20 \
    --lm models/char_5gram_lm.pkl \
    --lm-weight $lm_weight \
    --output results/a3_lm${lm_weight}.json
done
```

### 3. Ensemble Best Models
```bash
# Average predictions from A2 and A3
python scripts/ensemble_models.py \
  --models checkpoints/a2_improved/best.pt checkpoints/a3_joint_ctc_attention/best.pt \
  --configs configs/a2_improved.yaml configs/a3_joint_ctc_attention.yaml \
  --split test \
  --output results/ensemble.json
```

**Expected:** Additional -0.2 to -0.4% CER

---

## 📊 Expected Performance Timeline

| Week | Model | Technique | CER | WER | Status |
|------|-------|-----------|-----|-----|--------|
| 0 | A2 (epoch 12) | Greedy | 6.24% | 24.85% | ✅ Current |
| 1 | A2 (epoch 50) | Greedy | ~5.5% | ~23% | 🔄 Training |
| 1 | A3 (epoch 50) | Greedy | ~4.8% | ~20% | 🔄 Training |
| 2 | A2 (epoch 100) | Greedy | ~5.0% | ~21% | ⏳ Pending |
| 2 | A3 (epoch 100) | Greedy | ~4.2% | ~18% | ⏳ Pending |
| 2 | A3 (epoch 100) | Beam-20 | ~3.7% | ~17% | ⏳ Pending |
| 3 | A3 (epoch 100) | Beam-20 + LM | **~3.0-3.5%** | **~15-16%** | 🎯 Target |
| 3 | Ensemble | Beam + LM | **~2.8-3.2%** | **~14-15%** | 🏆 Stretch |

---

## 🚀 Quick Reference Commands

### Training
```bash
# A2 (already running)
tail -f logs/a2_improved/train.log

# Start A3
python scripts/train.py --config configs/a3_joint_ctc_attention.yaml --no-resume

# Resume if interrupted
python scripts/train.py --config configs/a3_joint_ctc_attention.yaml --resume auto
```

### Evaluation
```bash
# Greedy (fast)
python scripts/evaluate.py \
  --config configs/a3_joint_ctc_attention.yaml \
  --checkpoint checkpoints/a3_joint_ctc_attention/best.pt \
  --split test \
  --output results/a3_test.json

# Beam search (better)
python scripts/evaluate.py \
  --config configs/a3_joint_ctc_attention.yaml \
  --checkpoint checkpoints/a3_joint_ctc_attention/best.pt \
  --split test \
  --decode-method beam \
  --beam-width 20 \
  --bootstrap-ci \
  --output results/a3_test_beam20.json
```

### Language Model
```bash
# Train
python scripts/train_char_lm.py \
  --n 5 \
  --output models/char_5gram_lm.pkl \
  --test

# Use in evaluation (when implemented)
python scripts/evaluate.py \
  --config configs/a3_joint_ctc_attention.yaml \
  --checkpoint checkpoints/a3_joint_ctc_attention/best.pt \
  --split test \
  --decode-method beam \
  --beam-width 20 \
  --lm models/char_5gram_lm.pkl \
  --lm-weight 0.3 \
  --output results/a3_beam_lm.json
```

### Monitoring
```bash
# GPU usage
nvidia-smi

# Training progress
watch -n 5 'tail -3 logs/a2_improved/a2_improved_metrics.csv; echo "---"; tail -3 logs/a3_joint_ctc_attention/a3_joint_ctc_attention_metrics.csv'

# Disk space
df -h
du -sh checkpoints/* logs/*
```

---

## 📋 Checklist

### Immediate (Today)
- [ ] Train character 5-gram LM
- [ ] Start A3 joint CTC-attention training
- [ ] Archive A1 baseline results
- [ ] Check A1 beam search results (if complete)

### Week 1
- [ ] Monitor A2 training (epoch 12 → 100)
- [ ] Monitor A3 training (epoch 0 → 50+)
- [ ] Evaluate at epoch milestones (20, 40, 60, 80, 100)
- [ ] Test beam search on A2 when complete

### Week 2
- [ ] Implement beam search + LM integration
- [ ] Test different beam widths (5, 10, 20, 50)
- [ ] Tune LM weight (0.1 to 0.5)
- [ ] Evaluate A3 with best settings

### Week 3
- [ ] Fine-tune hyperparameters
- [ ] Test ensemble methods
- [ ] Final evaluation with all techniques
- [ ] Document best configuration

---

## 🎯 Success Criteria

**Minimum Acceptable:**
- CER: <5.0%
- WER: <21%

**Target:**
- CER: <4.0%
- WER: <18%

**Stretch Goal:**
- CER: <3.0%
- WER: <15%

---

## 📞 Troubleshooting

### If Training is Slow
```bash
# Check GPU usage
nvidia-smi

# Reduce batch size if OOM
# Edit config: batch_size: 32 → 24

# Use fewer workers if CPU bottleneck
# Edit config: num_workers: 4 → 2
```

### If Results Plateau
```bash
# Try longer training
num_epochs: 100 → 150

# Increase augmentation
elastic_p: 0.6 → 0.7

# Reduce learning rate
lr: 0.0002 → 0.0001
```

### If Overfitting
```bash
# Increase dropout
dropout: 0.3 → 0.4

# Increase weight decay
weight_decay: 0.00005 → 0.0001

# More augmentation
```

---

## 📖 Additional Resources

- **Documentation:** `IMPROVEMENTS.md`, `ADVANCED_IMPROVEMENTS.md`
- **Configs:** `configs/a*.yaml`
- **Scripts:** `scripts/*.py`
- **Models:** `checkpoints/`, `models/`
- **Results:** `results/`, `archive/`

---

## ✅ Summary

**Current:** 6.24% CER, 24.85% WER (A2 epoch 12)

**Next Steps:**
1. Build character LM ← **10 minutes**
2. Start A3 training ← **5 minutes**
3. Wait for training to complete ← **~3-4 days**
4. Evaluate with beam search + LM ← **1 hour**

**Expected Final:** ~3.0-3.5% CER, ~15-16% WER 🎯

**Timeline:** 2-3 weeks to achieve target

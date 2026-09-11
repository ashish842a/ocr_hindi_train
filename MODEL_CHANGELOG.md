# Model Version Changelog
**Hindi Handwritten Text Recognition (HTR) System**

This document tracks all model versions, architectural changes, and experimental configurations for reproducibility and ablation studies.

---

## 📋 Quick Version Summary

| Version | Date | Charset | Architecture | CER (%) | WER (%) | Status | Archive |
|---------|------|---------|--------------|---------|---------|--------|---------|
| **v1** | 2026-09-10 | 72 chars | ResNet50+BiLSTM+CTC | 46.08 | 78.02 | ❌ Failed | `experiments/archive/v1_charset72_*` |
| **v2** | 2026-09-10 | 100 chars | ResNet50+BiLSTM+CTC | TBD | TBD | 🔄 Current | - |
| **v3** | TBD | 100 chars | ResNet50+BiLSTM+CTC+Aug | TBD | TBD | 📝 Planned | - |
| **v4** | TBD | 100 chars | ResNet50+BiLSTM+Joint | TBD | TBD | 📝 Planned | - |

---

## Version 1: Baseline (Charset Issue) ❌

### 📅 Metadata
- **Version**: v1_charset72
- **Date**: 2026-09-10
- **Status**: Failed (incomplete charset)
- **Archive**: `experiments/archive/v1_charset72_20260910_162923/`

### 🏗️ Model Architecture
```
Input: RGB Images (H=64, W=variable)
    ↓
ResNet50 Backbone (pretrained)
  - conv1 + maxpool: stride /4
  - layer1: stride /1
  - layer2: stride /2
  - layer3: stride /2 (modified to (2,1) - HEIGHT only)
  - layer4: stride /2 (modified to (2,1) - HEIGHT only)
  - Total stride: /8 width, /16 height
  - Output: [B, 2048, H/16, W/8]
    ↓
Height Pooling: mean(dim=2)
  - Output: [B, 2048, W/8]
    ↓
BiLSTM Neck (2 layers, 512 hidden)
  - Bidirectional LSTM
  - Output: [B, W/8, 1024]
    ↓
CTC Head (dropout=0.3)
  - Linear: 1024 → 74 classes (72 chars + blank + unk)
  - Output: [B, W/8, 74]
    ↓
CTC Loss
```

### ⚙️ Configuration
```yaml
Model:
  backbone_type: resnet50
  backbone_config:
    pretrained: true
    fix_stride: true        # ✓ Key fix: (2,1) stride in layer3+4
    frozen_stages: 0

  neck_type: bilstm
  neck_config:
    hidden_dim: 512
    num_layers: 2
    dropout: 0.3

  head_type: ctc
  head_config:
    dropout: 0.3

Data:
  charset_size: 74 (72 chars + blank + unk)  # ❌ Problem: missing 28 chars
  min_char_freq: 50                           # ❌ Too high
  target_height: 64
  normalize: true (NFC Unicode)

Training:
  optimizer: Adam
  learning_rate: 0.0001
  batch_size: 32
  num_epochs: 50
  use_amp: true
  grad_clip: 5.0
  augmentation: false
```

### 📊 Results
```
Training (50 epochs, 2.1 hours):
  - Train Loss: 0.0058 (epoch 50)
  - Val Loss: 0.158 (best at epoch 45)
  - Total Parameters: 40,406,182
  - Training Time: 2.1 hours

Test Evaluation:
  - CER: 46.08% [45.63%, 46.56%] (95% CI)
  - WER: 78.02% [77.34%, 78.76%] (95% CI)
  - Samples: 12,869

Status: ❌ FAILED - Missing characters in charset
```

### 🔍 Issue Analysis
**Problem**: Used `min_char_freq=50` which excluded 28 rare but important characters.

**Evidence**:
```
Expected charset: 100 characters
Actual charset: 72 characters
Missing: 28 characters (28% of vocabulary)

Example errors:
  REF: प्रतिभावान  →  HYP: फतिाशा  (missing conjuncts)
  REF: सुसरालजनों  →  HYP: खुखरा    (missing characters)
  REF: ऊर्ध्वगामी  →  HYP: ऊधूीयत   (missing diacritics)
```

### 🔄 How to Reproduce
```bash
# 1. Prepare data (incorrect - for reproduction only)
python3 scripts/prepare_data_simple.py \
    --data-root dataset \
    --output-dir data_processed \
    --min-char-freq 50 \
    --normalize

# 2. Train
./scripts/train_with_log.sh configs/a1_baseline.yaml

# 3. Evaluate
./scripts/evaluate_with_log.sh \
    --config configs/a1_baseline.yaml \
    --checkpoint checkpoints/a1_baseline/best.pt \
    --split test \
    --output results/a1_test.json

# 4. Archive
./experiments/archive_experiment.sh v1_charset72 "Baseline with 72 chars (failed)"
```

### 📁 Archived Files
```
experiments/archive/v1_charset72_20260910_162923/
├── checkpoints/
│   ├── best.pt (epoch 45)
│   ├── latest.pt
│   └── epoch_*.pt
├── logs/
│   ├── a1_baseline_metrics.csv
│   └── a1_baseline_metrics.json
├── terminal_logs/
│   ├── a1_baseline_terminal_*.log
│   └── a1_baseline_eval_*.log
├── results/
│   ├── a1_test.json
│   └── a1_test.predictions.txt
├── data_processed/
│   ├── charset.json (72 chars)
│   └── charset.txt
├── config.yaml
└── EXPERIMENT_INFO.txt
```

---

## Version 2: Baseline (Corrected) 🔄

### 📅 Metadata
- **Version**: v2_charset100
- **Date**: 2026-09-10
- **Status**: In Progress / To Be Run
- **Archive**: TBD

### 🏗️ Model Architecture
```
[SAME AS V1 - only charset changed]

CTC Head (dropout=0.3)
  - Linear: 1024 → 102 classes (100 chars + blank + unk)  # ✓ CHANGED
  - Output: [B, W/8, 102]
```

### ⚙️ Configuration Changes from v1

**🔴 Changed**:
```yaml
Data:
  charset_size: 102 (100 chars + blank + unk)  # ✓ Fixed: all chars included
  min_char_freq: 1                             # ✓ Changed from 50 to 1
```

**🟢 Unchanged**:
```yaml
Model: [Same as v1]
Training: [Same as v1]
```

### 📊 Expected Results
```
Based on paper baseline:
  - Expected CER: 12-14%
  - Expected WER: 25-28%
  - Training Time: ~2-3 hours (50 epochs)
```

### 🔄 How to Run
```bash
# 1. Clean previous experiment
rm -rf checkpoints/a1_baseline/ logs/a1_baseline/ results/

# 2. Prepare data (CORRECTED)
python3 scripts/prepare_data_simple.py \
    --data-root dataset \
    --output-dir data_processed \
    --min-char-freq 1 \
    --normalize

# Verify charset size
wc -l data_processed/charset.txt  # Should show: 100

# 3. Train
./scripts/train_with_log.sh configs/a1_baseline.yaml

# 4. Evaluate
./scripts/evaluate_with_log.sh \
    --config configs/a1_baseline.yaml \
    --checkpoint checkpoints/a1_baseline/best.pt \
    --split test \
    --output results/a1_test.json

# 5. Archive
./experiments/archive_experiment.sh v2_charset100 "Baseline with 100 chars (corrected)"
```

---

## Version 3: With Data Augmentation 📝

### 📅 Metadata
- **Version**: v3_augmentation
- **Date**: TBD (Planned)
- **Status**: Planned
- **Archive**: TBD

### ⚙️ Configuration Changes from v2

**🔴 Changed**:
```yaml
Training:
  augmentation: true              # ✓ CHANGED from false

Augmentation:
  enabled: true
  random_rotation: 2.0            # degrees
  random_affine:
    scale: [0.9, 1.1]
    shear: 2.0
  elastic_transform:
    alpha: 10.0
    sigma: 3.0
```

**🟢 Unchanged**:
```yaml
Model: [Same as v2]
Data: [Same as v2]
```

### 🔄 How to Run
```bash
# Use augmentation config
./scripts/train_with_log.sh configs/a2_augmentation.yaml

./scripts/evaluate_with_log.sh \
    --config configs/a2_augmentation.yaml \
    --checkpoint checkpoints/a2_augmentation/best.pt \
    --split test \
    --output results/a2_test.json

./experiments/archive_experiment.sh v3_augmentation "With data augmentation"
```

### 📊 Expected Improvement
```
Expected CER improvement: 1-2% better than v2
Expected WER improvement: 2-3% better than v2
```

---

## Version 4: Joint CTC-Attention 📝

### 📅 Metadata
- **Version**: v4_joint_attention
- **Date**: TBD (Planned)
- **Status**: Planned
- **Archive**: TBD

### 🏗️ Model Architecture Changes

**🔴 Changed**:
```
BiLSTM Neck (same)
    ↓
  [SPLIT]
    ↓                      ↓
CTC Head            Attention Head
    ↓                      ↓
CTC Loss (0.7)      Attention Loss (0.3)
    ↓                      ↓
      Joint Loss = 0.7*CTC + 0.3*Attention
```

### ⚙️ Configuration Changes from v2

**🔴 Changed**:
```yaml
Model:
  head_type: joint              # ✓ CHANGED from ctc

  head_config:
    attention_dim: 512
    num_decoder_layers: 2
    max_decode_length: 50

Training:
  ctc_weight: 0.7              # ✓ NEW
  attention_weight: 0.3        # ✓ NEW
```

### 🔄 How to Run
```bash
./scripts/train_with_log.sh configs/a5_joint_ctc_attention.yaml

./scripts/evaluate_with_log.sh \
    --config configs/a5_joint_ctc_attention.yaml \
    --checkpoint checkpoints/a5_joint_ctc_attention/best.pt \
    --split test \
    --output results/a5_test.json

./experiments/archive_experiment.sh v4_joint_attention "Joint CTC-Attention"
```

---

## 📊 Results Comparison

### Performance Metrics

| Version | Charset | Aug | Architecture | CER (%) | WER (%) | Δ CER | Δ WER |
|---------|---------|-----|--------------|---------|---------|-------|-------|
| v1      | 72      | No  | ResNet+BiLSTM+CTC | 46.08 | 78.02 | - | - |
| v2      | 100     | No  | ResNet+BiLSTM+CTC | TBD | TBD | TBD | TBD |
| v3      | 100     | Yes | ResNet+BiLSTM+CTC | TBD | TBD | TBD | TBD |
| v4      | 100     | Yes | ResNet+BiLSTM+Joint | TBD | TBD | TBD | TBD |

### Training Efficiency

| Version | Params | Time/Epoch | Total Time | GPU Memory |
|---------|--------|------------|------------|------------|
| v1      | 40.4M  | ~150s      | 2.1h       | ~8-10GB    |
| v2      | 40.4M  | TBD        | TBD        | ~8-10GB    |
| v3      | 40.4M  | TBD        | TBD        | ~8-10GB    |
| v4      | ~42M   | TBD        | TBD        | ~8-10GB    |

---

## 🔧 Common Operations

### View Version Differences
```bash
# Compare configs
diff experiments/archive/v1_*/config.yaml experiments/archive/v2_*/config.yaml

# Compare charsets
diff experiments/archive/v1_*/data_processed/charset.txt \
     experiments/archive/v2_*/data_processed/charset.txt
```

### Analyze Version Performance
```bash
# View training curves
python scripts/view_training_logs.py --log-dir experiments/archive/v2_*/logs

# Compare predictions
head -50 experiments/archive/v1_*/results/a1_test.predictions.txt
head -50 experiments/archive/v2_*/results/a1_test.predictions.txt
```

### Reproduce Any Version
```bash
# See "How to Run" section for each version above
# Each version has complete reproduction commands
```

---

## 📝 Adding New Versions

### Template for New Version:

```markdown
## Version X: [Name] [Status Emoji]

### 📅 Metadata
- **Version**: vX_name
- **Date**: YYYY-MM-DD
- **Status**: [Planned/In Progress/Complete/Failed]
- **Archive**: path or TBD

### 🏗️ Model Architecture
[Describe architecture or changes]

### ⚙️ Configuration Changes from vN
**🔴 Changed**:
[List changes]

**🟢 Unchanged**:
[List what stayed same]

### 📊 Results
[Add results when available]

### 🔄 How to Run
[Complete reproduction commands]
```

---

## 🎯 Key Insights

### v1 → v2: Charset Size Impact
- **Change**: 72 → 100 characters (28 more chars)
- **Impact**: Expected ~34% CER reduction (46% → 12%)
- **Lesson**: Character coverage is critical for Devanagari script
- **Why**: Missing conjuncts and rare diacritics caused failures

### Future Ablations
- [ ] Learning rate scheduling
- [ ] Batch size impact (16, 32, 64)
- [ ] Backbone depth (ResNet34 vs ResNet50)
- [ ] BiLSTM layers (1, 2, 3)
- [ ] Dropout rates (0.1, 0.3, 0.5)

---

**Last Updated**: 2026-09-10
**Next Update**: After v2 training completes

# Advanced Improvements to Minimize CER & WER

**Current Performance (Epoch 12):**
- CER: 6.24%
- WER: 24.85%

**Target Performance:**
- CER: <4.0% (35% improvement)
- WER: <18% (28% improvement)

---

## 🎯 High-Impact Improvements (Ranked by ROI)

### 1. **Joint CTC-Attention Architecture** ⭐⭐⭐⭐⭐
**Impact:** -1.0 to -1.5% CER, -3 to -5% WER
**Difficulty:** Easy (already implemented!)
**Implementation time:** 5 minutes

Your codebase already supports joint CTC-Attention training!

**Why it helps:**
- CTC handles alignment uncertainty
- Attention models sequential dependencies
- Together they complement each other's weaknesses
- Attention is particularly good for WER (word-level accuracy)

**How to implement:**
```yaml
# configs/a3_joint_ctc_attention.yaml
model:
  head_type: joint  # Changed from 'ctc'

  head_config:
    ctc_config:
      dropout: 0.3
    attention_config:
      decoder_dim: 512
      attention_dim: 256
      dropout: 0.3

training:
  ctc_weight: 0.7  # Balance between CTC and Attention
  # Rest same as a2_improved.yaml
```

**Training command:**
```bash
python scripts/train.py --config configs/a3_joint_ctc_attention.yaml --no-resume
```

---

### 2. **Character-Level Language Model** ⭐⭐⭐⭐⭐
**Impact:** -0.8 to -1.2% CER, -2 to -4% WER
**Difficulty:** Medium
**Implementation time:** 2-3 hours

Build a character n-gram model from training data to constrain predictions to valid Hindi sequences.

**Implementation:**

```python
# src/hindi_htr/decode/language_model.py
import pickle
from collections import defaultdict, Counter
from typing import List, Tuple

class CharNGramLM:
    """Character-level n-gram language model for Hindi."""

    def __init__(self, n: int = 3):
        self.n = n
        self.ngrams = defaultdict(Counter)
        self.vocab = set()

    def train(self, texts: List[str]):
        """Train on list of texts."""
        for text in texts:
            text = '<' * (self.n - 1) + text + '>'  # Add padding
            self.vocab.update(text)

            for i in range(len(text) - self.n + 1):
                context = text[i:i+self.n-1]
                char = text[i+self.n-1]
                self.ngrams[context][char] += 1

        # Normalize to probabilities
        for context in self.ngrams:
            total = sum(self.ngrams[context].values())
            for char in self.ngrams[context]:
                self.ngrams[context][char] /= total

    def score(self, text: str) -> float:
        """Score a text with log probability."""
        text = '<' * (self.n - 1) + text + '>'
        log_prob = 0.0

        for i in range(len(text) - self.n + 1):
            context = text[i:i+self.n-1]
            char = text[i+self.n-1]

            if context in self.ngrams and char in self.ngrams[context]:
                prob = self.ngrams[context][char]
            else:
                prob = 1e-6  # Small smoothing

            log_prob += np.log(prob)

        return log_prob

    def save(self, path: str):
        with open(path, 'wb') as f:
            pickle.dump((self.n, self.ngrams, self.vocab), f)

    @classmethod
    def load(cls, path: str):
        with open(path, 'rb') as f:
            n, ngrams, vocab = pickle.load(f)
        lm = cls(n=n)
        lm.ngrams = ngrams
        lm.vocab = vocab
        return lm

# Train the LM
import json
texts = []
with open('data_processed/train_manifest.jsonl') as f:
    for line in f:
        texts.append(json.loads(line)['text'])

lm = CharNGramLM(n=5)  # 5-gram
lm.train(texts)
lm.save('models/char_5gram_lm.pkl')
```

**Beam search with LM:**
```python
# Modify beam_search.py to incorporate LM scores
def beam_search_with_lm(logits, charset, beam_width=10, lm=None, lm_weight=0.3):
    # Score = (1 - lm_weight) * ctc_score + lm_weight * lm_score
    pass
```

---

### 3. **Test-Time Augmentation (TTA)** ⭐⭐⭐⭐
**Impact:** -0.3 to -0.6% CER, -0.5 to -1.0% WER
**Difficulty:** Easy
**Implementation time:** 30 minutes

Average predictions across multiple augmented versions of each test image.

```python
# src/hindi_htr/engine/evaluator.py
class TTAEvaluator(Evaluator):
    def predict_with_tta(self, images, input_lengths, num_augmentations=5):
        predictions_all = []

        for _ in range(num_augmentations):
            # Apply random augmentation
            aug_images = self.augment(images)
            preds = self.predict(aug_images, input_lengths)
            predictions_all.append(preds)

        # Vote or average predictions
        final_preds = self.ensemble_predictions(predictions_all)
        return final_preds
```

---

### 4. **Longer Context Training** ⭐⭐⭐⭐
**Impact:** -0.5 to -0.8% CER
**Difficulty:** Easy
**Implementation time:** 5 minutes

Increase BiLSTM layers to capture longer dependencies.

```yaml
# configs/a4_deeper_lstm.yaml
model:
  neck_config:
    hidden_dim: 512
    num_layers: 3  # Increased from 2
    dropout: 0.3
```

---

### 5. **Transformer Neck** ⭐⭐⭐⭐
**Impact:** -0.5 to -1.0% CER, -1 to -2% WER
**Difficulty:** Easy (already implemented!)
**Implementation time:** 5 minutes

Transformers capture long-range dependencies better than LSTMs.

```yaml
# configs/a5_transformer.yaml
model:
  neck_type: transformer  # Changed from 'bilstm'

  neck_config:
    hidden_dim: 512
    num_layers: 4
    num_heads: 8
    dim_feedforward: 2048
    dropout: 0.1
```

---

### 6. **Multi-Scale Features** ⭐⭐⭐
**Impact:** -0.3 to -0.5% CER
**Difficulty:** Medium
**Implementation time:** 2 hours

Extract features from multiple ResNet layers for richer representations.

```python
# Modify ResNetBackbone to return multi-scale features
class MultiScaleResNetBackbone(nn.Module):
    def forward(self, x):
        x1 = self.resnet.layer1(x)  # 1/4
        x2 = self.resnet.layer2(x1) # 1/8
        x3 = self.resnet.layer3(x2) # 1/16
        x4 = self.resnet.layer4(x3) # 1/16

        # Fuse features
        x2_up = F.interpolate(x2, size=x4.shape[-2:])
        x3_up = F.interpolate(x3, size=x4.shape[-2:])

        fused = torch.cat([x2_up, x3_up, x4], dim=1)
        return fused
```

---

### 7. **CTC Blank Penalty** ⭐⭐⭐
**Impact:** -0.2 to -0.4% CER
**Difficulty:** Easy
**Implementation time:** 15 minutes

Penalize blank predictions during beam search to encourage more characters.

```python
def beam_search_decode(logits, charset, blank_penalty=0.1):
    # Reduce blank token probability
    logits[:, :, blank_idx] -= blank_penalty
    # Continue with normal beam search
```

---

### 8. **Focal CTC Loss** ⭐⭐⭐
**Impact:** -0.3 to -0.5% CER
**Difficulty:** Medium
**Implementation time:** 1 hour

Focus training on hard examples.

```python
class FocalCTCLoss(nn.Module):
    def __init__(self, alpha=0.25, gamma=2.0):
        super().__init__()
        self.alpha = alpha
        self.gamma = gamma
        self.ctc = nn.CTCLoss()

    def forward(self, logits, targets, input_lengths, target_lengths):
        # Compute CTC loss
        loss = self.ctc(logits, targets, input_lengths, target_lengths)

        # Apply focal weighting
        p = torch.exp(-loss)
        focal_weight = self.alpha * (1 - p) ** self.gamma

        return focal_weight * loss
```

---

### 9. **Label Smoothing** ⭐⭐⭐
**Impact:** -0.2 to -0.3% CER
**Difficulty:** Easy
**Implementation time:** 20 minutes

Prevent overconfident predictions.

```python
class CTCLossWithLabelSmoothing(nn.Module):
    def __init__(self, smoothing=0.1):
        super().__init__()
        self.smoothing = smoothing
        self.ctc = nn.CTCLoss()

    def forward(self, logits, targets, input_lengths, target_lengths):
        # Mix hard labels with uniform distribution
        # ... implementation
```

---

### 10. **Semi-Supervised Learning** ⭐⭐⭐⭐
**Impact:** -0.5 to -1.0% CER (if unlabeled data available)
**Difficulty:** Hard
**Implementation time:** 1 day

If you have unlabeled Hindi word images:
1. Train on labeled data
2. Pseudo-label unlabeled data
3. Retrain on combined dataset

---

## 📋 Recommended Implementation Order

### **Phase 1: Quick Wins (Week 1)**
1. ✅ **Joint CTC-Attention** - Start training immediately
2. ✅ **Deeper LSTM** (3 layers) - Easy config change
3. ✅ **CTC Blank Penalty** - Quick beam search improvement

**Expected after Phase 1:** CER ~5.0-5.5%, WER ~21-23%

### **Phase 2: Medium Effort (Week 2)**
4. **Character N-Gram LM** - Build and integrate
5. **Test-Time Augmentation** - Implement TTA evaluation
6. **Transformer Neck** - Alternative architecture

**Expected after Phase 2:** CER ~4.0-4.5%, WER ~18-20%

### **Phase 3: Advanced (Week 3-4)**
7. **Multi-Scale Features** - ResNet enhancement
8. **Focal Loss** - Better hard example learning
9. **Label Smoothing** - Regularization

**Expected after Phase 3:** CER ~3.5-4.0%, WER ~16-18%

---

## 🎯 Target Achievement Plan

| Technique | CER Impact | WER Impact | Cumulative CER | Cumulative WER |
|-----------|------------|------------|----------------|----------------|
| **Baseline (A2)** | - | - | 6.24% | 24.85% |
| + Joint CTC-Attention | -1.2% | -4.0% | 5.04% | 20.85% |
| + Beam Search (width=10) | -0.5% | -1.5% | 4.54% | 19.35% |
| + Character LM | -0.8% | -2.0% | 3.74% | 17.35% |
| + TTA | -0.3% | -0.5% | 3.44% | 16.85% |
| + Transformer Neck | -0.5% | -1.0% | **2.94%** | **15.85%** |

---

## 🚀 Immediate Action Items

### **1. Start Joint CTC-Attention Training NOW**

Create config:
```bash
cat > configs/a3_joint_ctc_attention.yaml << 'EOF'
# Copy all from a2_improved.yaml, then modify:

model:
  head_type: joint
  head_config:
    ctc_config:
      dropout: 0.3
    attention_config:
      decoder_dim: 512
      attention_dim: 256
      dropout: 0.3

training:
  ctc_weight: 0.7
  # ... rest same as a2_improved.yaml
EOF
```

Start training:
```bash
python scripts/train.py --config configs/a3_joint_ctc_attention.yaml --no-resume
```

### **2. Build Character Language Model**

```bash
# Create training script
cat > scripts/train_char_lm.py << 'EOF'
import json
from src.hindi_htr.decode.language_model import CharNGramLM

# Load training texts
texts = []
with open('data_processed/train_manifest.jsonl') as f:
    for line in f:
        texts.append(json.loads(line)['text'])

# Train 5-gram LM
lm = CharNGramLM(n=5)
lm.train(texts)
lm.save('models/char_5gram_lm.pkl')
print(f"Trained on {len(texts)} samples")
EOF

python scripts/train_char_lm.py
```

### **3. Test Current Model with Beam Search**

```bash
# Test A2 with beam search
python scripts/evaluate.py \
  --config configs/a2_improved.yaml \
  --checkpoint checkpoints/a2_improved/best.pt \
  --split test \
  --decode-method beam \
  --beam-width 20 \
  --output results/a2_beam20_test.json
```

---

## 📊 Expected Timeline

- **Now:** CER 6.24%, WER 24.85%
- **Epoch 50:** CER ~5.5%, WER ~23% (greedy)
- **Epoch 100:** CER ~5.0%, WER ~21% (greedy)
- **+ Joint Attention (100 epochs):** CER ~4.0%, WER ~18%
- **+ Beam + LM:** CER ~3.0-3.5%, WER ~15-17%

---

## 🎓 Key Insights

1. **Joint CTC-Attention** is the single biggest improvement you can make
2. **Language models** are crucial for reducing WER (word errors)
3. **Beam search** alone gives 10-15% relative improvement
4. **Your current training (A2) should continue** - it will reach ~5% CER
5. **WER** improves faster than CER with attention + LM

---

## ✅ Summary

**Highest Priority (Do First):**
1. Continue A2 training to epoch 100
2. Start A3 (Joint CTC-Attention) training in parallel
3. Build character n-gram language model
4. Test beam search on completed models

**Expected Final Results:**
- **Greedy CTC:** ~5.0% CER, ~21% WER
- **Joint CTC-Attention:** ~4.0% CER, ~18% WER
- **+ Beam Search + LM:** **~3.0-3.5% CER, ~15-17% WER**

This would put you in the **top tier of Hindi HTR systems**! 🏆

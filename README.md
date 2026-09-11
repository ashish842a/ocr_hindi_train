# Hindi HTR - Handwritten Text Recognition for Devanagari

M.Tech research project: Gap analysis and improvements on ResNet50-BiLSTM-CTC for Hindi handwriting recognition.

## Overview

This repository implements a reproducible Hindi HTR system that addresses 8 documented gaps (G1-G8) in Khan et al. (2026), with 6 concrete contributions (C1-C6):

- **C1**: Corrected ResNet50-BiLSTM-CTC baseline with stride fix
- **C2**: Properly specified joint CTC-Attention model
- **C3**: Akshara-aware modeling and evaluation
- **C4**: Four-regime decoding study (greedy/beam/lexicon-constrained)
- **C5**: Writer-invariant training via gradient reversal
- **C6**: Full reproducibility package (seeds, logs, bootstrap CIs)

**Key finding**: The paper's published architecture (ResNet50 stride /32) cannot train - CTC loss is undefined for 66.7% of the training set. Our stride-(2,1) fix reduces failure rate to 0%.

## Repository Structure

```
ocr_hindi/                    # Repo root
├── dataset/                  # IIIT-HW-Hindi_v1 (git-ignored)
├── papers/                   # Reference PDFs
├── plan/                     # PLAN.md, plan.html
├── configs/                  # YAML configs (base, a0-a8, p1)
├── src/hindi_htr/           # Source code
│   ├── data/                # manifest, charset, dataset, transforms, sampler
│   ├── models/              # backbones, necks, heads, model
│   ├── losses/              # CTC, attention, joint
│   ├── decode/              # greedy, beam search
│   ├── metrics/             # CER, WER, bootstrap
│   ├── engine/              # trainer, evaluator
│   └── utils/               # device, seed, logging, config
├── scripts/
│   ├── prepare_data.py      # Phase P0 - data prep (CPU-only)
│   ├── train.py             # Main training script
│   └── evaluate.py          # Evaluation with CIs
├── notebooks/               # Colab training notebook (TBD)
├── requirements.txt         # Local CUDA environment
├── requirements-colab.txt   # Google Colab
└── .gitignore
```

## Quick Start

### 1. Data Preparation (Phase P0)

Runs on CPU - no GPU required:

```bash
python scripts/prepare_data.py \
    --data-root dataset/IIIT-HW-Hindi_v1 \
    --output-dir data_processed \
    --min-char-freq 50 \
    --normalize
```

Outputs:
- `data_processed/train_manifest.jsonl`
- `data_processed/val_manifest.jsonl`
- `data_processed/test_manifest.jsonl`
- `data_processed/charset.json`
- `data_processed/statistics.json`

### 2. Training

**A0 (Paper as written - will fail):**
```bash
python scripts/train.py --config configs/a0_paper_asis.yaml
```

**A1 (Corrected baseline):**
```bash
python scripts/train.py --config configs/a1_baseline.yaml
```

**A5 (Joint CTC-Attention):**
```bash
python scripts/train.py --config configs/a5_joint_ctc_attention.yaml
```

### 3. Evaluation

```bash
python scripts/evaluate.py \
    --config configs/a1_baseline.yaml \
    --checkpoint checkpoints/a1_baseline/best.pt \
    --split test \
    --decode-method greedy \
    --bootstrap-ci \
    --output results/a1_test.json
```

## Ablation Grid

| ID | Configuration | Isolates |
|----|---------------|----------|
| **A0** | ResNet50 /32 + BiLSTM + CTC (paper as written) | G1 evidence |
| **A1** | ResNet50 (2,1)-stride + BiLSTM + CTC | Corrected baseline |
| A2 | A1 + augmentation | Augmentation |
| A3 | A2 + NFC + charset pruning | G3 |
| A4 | A3 + Transformer encoder | G2 reading 1 |
| **A5** | A3 + Joint CTC-Attention | G2 reading 2 |
| A6 | A5 + Akshara vocabulary | G4 |
| A7 | A6 + Writer adversary | G6 |
| **A8** | A7 + Lexicon-constrained decoding | G5 |

## Environment Setup

**Python 3.11 or 3.12 required** (PyTorch has no wheels for 3.14).

### Local CUDA

```bash
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Google Colab

Upload dataset to Google Drive, then:

```python
!pip install -r requirements-colab.txt
```

## Dataset

**IIIT-HW-Hindi v1** - 95,430 word images, 12 writers, writer-disjoint splits.

- Train: 69,853 images (writers 1,2,4,5,7,8,10)
- Val: 12,708 images (writers 3,12)
- Test: 12,869 images (writers 6,9,11)

**Important**: This is a **closed-vocabulary** benchmark - all test words appear in training. Lexicon-constrained decoding results must be clearly labeled.

## Citation

```
@misc{kumar2026hindihtr,
  author = {Kumar, Ashish},
  title = {Hindi HTR: Gap Analysis of ResNet50-BiLSTM-CTC},
  year = {2026},
  url = {https://github.com/...}
}
```

Reference paper: Khan et al., "Handwritten Text Recognition..." Procedia CS 283 (2026) 3040-3048.

## License

MIT License - see LICENSE file for details.

## Contact

Ashish Kumar - M.Tech Student
For questions about this implementation, open an issue on GitHub.

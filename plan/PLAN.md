# Hindi Handwritten Text Recognition — Gap Analysis & Research Plan

**Reference paper:** Khan, Ansari, Ahmad, Bilal — *"Handwritten Hindi Text Recognition using ResNet50-BiLSTM"*, Procedia Computer Science 283 (2026) 3040–3048, ICMLDE. Reported **CER 9.0% / WER 18.0%** on IIIT-HW.

**Our dataset:** `dataset/IIIT-HW-Hindi_v1` — the same corpus the paper uses (95,430 word images, 12 writers).

**Repo root:** `Mtech/code/ocr_hindi/` — this directory is now its own git repository (`main`, no commits yet) and holds `dataset/`, `papers/`, `plan/`, and, going forward, all source code directly (no extra `code/ocr_hindi/` nesting — see §6). `.gitignore` is already in place and correctly excludes `dataset/`, `data/`, checkpoints, logs, venvs, and OS/editor cruft.

**Author:** Ashish Kumar · M.Tech
**Status:** planning — no source code written yet
**Date:** 2026-09-08

---

## 0. Executive summary

I audited the paper against the actual dataset on disk. The paper has **one fatal reproducibility defect, one incoherent architectural claim, and five methodological omissions** — all of which are measurable on this dataset and all of which are fixable. The most important finding:

> **The architecture as described in the paper cannot train.** A stock ResNet50 downsamples by 32× in *both* dimensions. Measured on 4,000 real training images at input height 64, the encoder emits a median of **5 time steps** for a median label of **6 characters**. CTC loss is mathematically undefined (infinite) whenever `T < required_length`. **66.7% of the training set falls in that regime.**

That defect alone means the published pipeline either (a) was not the pipeline actually run, or (b) silently dropped two-thirds of the data. Fixing it is not a tweak — it is the precondition for everything else. It also plausibly explains why their CER plateaus at 9% when comparable Indic HTR systems reach 4–6%.

My plan: build a genuinely correct and reproducible baseline, then stack five improvements that each target a documented gap, with an ablation isolating every one.

**Targets:** CER ≤ 5%, WER ≤ 12% (unconstrained) · WER ≤ 6% (lexicon-constrained) — versus the paper's 9.0 / 18.0.

---

## 1. What the paper actually proposes

| Component | Paper's specification |
|---|---|
| Encoder | ResNet50 pretrained on ImageNet, 2048-d feature maps reshaped to a sequence |
| Sequence model | 2-layer BiLSTM, 512 hidden units per direction (1024 total) |
| Attention | Additive / Bahdanau, 256-unit alignment network, applied on BiLSTM outputs |
| Loss | CTC |
| Decoding | Beam search, beam width 10, "character-level language model provided further help" |
| Optimiser | Adam, lr 1e-4 (§4.1) — but §3.5 says lr 0.001 |
| Training | batch 32, 50 epochs, dropout 0.3, grad clip 5.0, early stop on val CER |
| Augmentation | elastic distortion, affine, perspective warp, random scaling |
| Preprocessing | grayscale, normalise, resize to fixed height preserving aspect ratio |
| Result | CER 9.0%, WER 18.0% |

Internal inconsistencies worth noting: the abstract says **CER 9.4 / WER 18.1**, the introduction says **9 / 18**, Table 1 says **9.0 / 18.0**; §3.5 says lr 0.001 while §4.1 says 1e-4; and Table 1's citation `[1] Sharma et al. (Handcrafted + HMM)` maps to *Graves et al., CTC, ICML 2006* in the actual bibliography — the comparison table's citations do not match its reference list.

---

## 2. Dataset ground truth (measured, not assumed)

Everything below was computed directly from `dataset/IIIT-HW-Hindi_v1`.

### 2.1 Splits and writers

| Split | Images | Writers | Word types | Pages |
|---|---|---|---|---|
| train | 69,853 | 7 — `1,2,4,5,7,8,10` | 9,539 | 1,843 |
| val | 12,708 | 2 — `3,12` | 8,603 | 337 |
| test | 12,869 | 3 — `6,9,11` | 6,931 | 344 |
| **total** | **95,430** | **12** | 11,030 (lexicon) | 2,524 |

All 95,430 image files referenced by the label lists exist on disk. No duplicate paths. Splits are **writer-disjoint** — a fact the paper never states, and which makes this a writer-independent benchmark.

Test set is writer-imbalanced: writer 9 → 5,572 images, writer 6 → 5,034, writer 11 → 2,263. A single aggregate CER is therefore dominated by two writers.

### 2.2 Images

| Property | min | p5 | p50 | p95 | max |
|---|---|---|---|---|---|
| width (px) | 311 | 503 | 734 | 1128 | 1946 |
| height (px) | 250 | 292 | 293 | 294 | 322 |
| aspect (w/h) | 1.06 | 1.72 | 2.51 | 3.85 | 6.64 |

Height is essentially constant (~293 px); **width is the only informative dimension.** Aspect ratio spans 6×, so fixed-size resizing destroys information and fixed-width padding wastes ~60% of every batch. Bucketed batching by aspect ratio is required, and CTC input lengths must be masked per sample — the paper discusses neither.

### 2.3 Labels

- Label length: min 1, mean 5.98, max 23 characters.
- Train charset: **108 Unicode codepoints**. After NFC normalisation: **100**. NFD: 97.
- **1,841 training labels change under NFC** — i.e. the same rendered word is stored two different ways.
- Concrete instance: `ड़` appears both precomposed as U+095C (906×) and decomposed as U+0921 + U+093C (nukta, 2,914 total occurrences).
- 32 characters occur fewer than 50 times and together account for **0.14%** of all character tokens. Several are annotation noise, not Hindi: `॓` (grave accent), `ॽ` (glottal stop), `ऴ` (LLLA — a Dravidian letter), `ॻ ॼ ॾ` (Sindhi implosives).
- **Zero out-of-vocabulary characters** in val or test relative to train.

### 2.4 The closed-vocabulary finding

> **0 of 6,931 test word types are unseen in training. 0 of 8,603 val types are unseen. All 95,430 labels are covered by the shipped 11,030-word lexicon.**

This is the single most consequential unstated property of the benchmark. It means a lexicon-constrained decoder can, in principle, never be wrong for the right reason — and it means the paper's WER of 18% is measured on a task where the answer is always in a list of 11,030 candidates that ships with the dataset. The paper mentions "a character-level language model" but never the lexicon, and never discloses the closure.

Any honest result on this dataset must report closed- and open-vocabulary numbers separately. I will do so, and I will construct a held-out-word-type protocol to measure genuine generalisation.

---

## 3. Gap analysis

### G1 — CTC is mathematically infeasible for 2/3 of the data · **severity: fatal**

Stock ResNet50 has total stride 32 (conv1 /2, maxpool /2, layer2 /2, layer3 /2, layer4 /2). Reshaping its output to a sequence gives `T = W/32` time steps. CTC requires `T ≥ len(label) + (number of adjacent repeated characters)`.

Measured over 4,000 random training images:

| Encoder configuration | T p5 | T p50 | T p95 | CTC-infeasible samples |
|---|---|---|---|---|
| H=64, ResNet50 unmodified (/32) | 3 | 5 | 7 | **66.70%** |
| H=128, ResNet50 unmodified (/32) | 6 | 10 | 15 | 0.45% |
| H=32, CRNN-style (/4 width) | 13 | 20 | 31 | 0.00% |
| **H=64, ResNet50 with (2,1) stride in layer3+layer4** | **27** | **40** | **62** | **0.00%** |

**Fix:** replace the stride-(2,2) downsampling in `layer3` and `layer4` with stride-(2,1) so height collapses but width is preserved at /4. This is standard CRNN practice and costs nothing. It is also entirely absent from the paper. I will report the paper's configuration *as an ablation row* to document the defect empirically.

### G2 — The attention mechanism as described is not a well-defined model · **severity: high**

The paper states additive Bahdanau attention over BiLSTM outputs, then CTC loss with beam search over the same outputs. These are incompatible as written: Bahdanau attention presupposes an autoregressive decoder with its own output time axis, whereas CTC requires a frame-synchronous, monotonic emission aligned to encoder frames. There is no equation, no shape specification, and — critically — **no ablation isolating the attention module's contribution.** The paper's central claim ("attention substantially enhances word-level recognition") is therefore unsupported by any reported experiment.

**Fix — two well-defined readings, both implemented and compared:**
1. **Self-attention encoder:** Transformer encoder layers stacked on the BiLSTM output. Frame count is preserved, CTC stays valid. This is the charitable reading of what they meant.
2. **Joint CTC–Attention (Watanabe-style):** a shared encoder with two heads — a CTC head and an autoregressive attention decoder — trained as `L = λ·L_ctc + (1−λ)·L_att`, and decoded by joint one-pass scoring. This is the architecture the paper gestures at but does not define, and it is the headline contribution of my work.

### G3 — No Unicode normalisation; metrics are not comparable · **severity: high**

With `ड़` stored two ways, an identical prediction scores differently depending on which encoding the ground truth happens to use, and the effective charset is inflated by 8 spurious classes. The paper never specifies a normalisation form, so its CER is not reproducible even in principle.

**Fix:** NFC-normalise every label at manifest build time; define and freeze an explicit charset; map the 32 sub-50-occurrence characters to `<unk>` or drop those samples (documented either way); report CER before and after normalisation to quantify the effect.

### G4 — Codepoint CER is the wrong metric for Devanagari · **severity: medium**

CER over Unicode codepoints scores a vowel sign (`ि`) as a full unit equal to a consonant. Devanagari is read as *akshara* — grapheme clusters like `कि`, `की`, `क्ष`. Confusing `कि` with `की` (one matra) and confusing `क` with `घ` (a whole consonant) currently cost the same.

**Fix:** report three metrics — codepoint CER, **grapheme-cluster CER (Akshara Error Rate)**, and WER — and additionally train a variant whose CTC output vocabulary is *akshara units* rather than codepoints, so the model predicts what a reader perceives. Neither the metric nor the tokenisation appears in the paper.

### G5 — Closed vocabulary is undisclosed and unexploited · **severity: high**

See §2.4. The paper leaves a large, free WER reduction on the table while also failing to disclose that the task is closed-vocabulary, which makes its Table 1 comparison against other papers unsound.

**Fix:** report four decoding regimes side by side — greedy, unconstrained beam, beam + character n-gram LM (shallow fusion), and **lexicon-constrained beam over a prefix trie of the 11,030-word lexicon** — plus an **open-vocabulary protocol** in which I hold out word types from training to measure true generalisation. Honest disclosure here is itself a methodological contribution.

### G6 — Writer-disjointness is never analysed · **severity: medium**

The splits are writer-disjoint and test is dominated by two of three writers, but the paper reports one aggregate number with no variance and no per-writer breakdown. Generalisation to an unseen hand is the actual difficulty of this benchmark and it goes unmeasured.

**Fix:** per-writer CER/WER tables with bootstrap confidence intervals; leave-one-writer-out cross-validation on the training writers; and a genuine modelling contribution — a **writer-adversarial branch** (gradient reversal on a writer-ID classifier) that forces the encoder toward writer-invariant features, plus classical slant/slope normalisation as a cheaper alternative.

### G7 — Reproducibility surface is absent · **severity: medium**

No code, no seeds, no training curves, no parameter count, no inference latency, no confidence intervals, contradictory hyperparameters between §3.5 and §4.1, contradictory headline numbers between abstract and results, and a comparison table whose citations do not match its bibliography and whose baselines were taken from other papers rather than re-run on a matched split.

**Fix:** fixed seeds, released code, deterministic manifests, per-epoch logs, params + latency columns, bootstrap CIs, and — importantly — **re-implementation of the CRNN/VGG-BiLSTM baseline on this exact split** so the comparison table is apples-to-apples.

### G8 — Variable-width batching is unaddressed · **severity: medium**

Aspect ratios span 1.06–6.64. Padding to a fixed width without passing per-sample input lengths to `CTCLoss` corrupts the loss; padding to max width in a shuffled batch wastes most of the compute. The paper says only "resize to constant height preserving aspect ratio" and stops.

**Fix:** aspect-ratio bucketed sampler, right-padding with an explicit `input_lengths` tensor, and padding-aware masking in both the BiLSTM (`pack_padded_sequence`) and the attention layers.

---

## 4. Contributions

| # | Contribution | Fills |
|---|---|---|
| C1 | Correct, reproducible ResNet-BiLSTM-CTC baseline with stride-corrected encoder, bucketed batching, and length masking — plus an empirical demonstration of the published configuration's failure | G1, G7, G8 |
| C2 | Properly specified **joint CTC–Attention** model (shared encoder, dual head, λ-weighted loss, joint decoding) with an ablation isolating attention's actual contribution | G2 |
| C3 | **Akshara-aware** modelling and evaluation: grapheme-cluster CTC vocabulary + Akshara Error Rate reported alongside codepoint CER | G4 |
| C4 | Four-regime decoding study with **lexicon-constrained beam search** and an explicit **open- vs closed-vocabulary protocol** | G5 |
| C5 | **Writer-invariant training** via gradient-reversal writer adversary, with per-writer breakdown and leave-one-writer-out CV | G6 |
| C6 | Full reproducibility package: seeds, configs, logs, bootstrap CIs, params/latency, re-run baselines on the matched split | G7 |

---

## 5. Experimental plan

### 5.1 Phases

| Phase | Goal | Key deliverable | Est. GPU time |
|---|---|---|---|
| **P0** | Data audit, manifest build, NFC normalisation, charset freeze, LMDB packing, bucket sampler | `data/manifests/*.jsonl`, `charset.json`, audit report | ~1 h CPU |
| **P1** | Small CRNN sanity baseline — proves the pipeline end to end on 5k samples | first CER number, training curve | ~1 h |
| **P2** | Paper reproduction: ResNet50-BiLSTM-CTC, both unmodified (/32) and stride-corrected. **Documents G1 empirically.** | reproduction table, G1 evidence | ~10 h |
| **P3** | Improvements: augmentation suite, akshara tokenisation, Transformer encoder on top of BiLSTM | ablation rows A1–A5 | ~20 h |
| **P4** | Joint CTC–Attention + writer-adversarial branch | main model checkpoint | ~20 h |
| **P5** | Decoding study: greedy / beam / char-LM fusion / lexicon-constrained; open-vocab protocol | decoding table | ~4 h |
| **P6** | Per-writer analysis, LOWO-CV, bootstrap CIs, error taxonomy, figures, write-up | thesis chapter + paper draft | — |

### 5.2 Ablation grid (the paper has none)

| ID | Configuration | Isolates |
|---|---|---|
| A0 | ResNet50 /32 + BiLSTM + CTC (paper as literally written) | G1 |
| A1 | ResNet50 (2,1)-stride + BiLSTM + CTC | corrected baseline |
| A2 | A1 + augmentation (elastic, affine, perspective, morphological) | augmentation |
| A3 | A2 + NFC normalisation + charset pruning | G3 |
| A4 | A3 + Transformer self-attention encoder | reading (1) of G2 |
| A5 | A3 + joint CTC–Attention decoder | reading (2) of G2 |
| A6 | A5 + akshara vocabulary | G4 |
| A7 | A6 + writer-adversarial branch | G6 |
| A8 | A7 + lexicon-constrained decoding | G5 |

Each row reports: codepoint CER, akshara CER, WER, params, latency, and a 95% bootstrap CI.

### 5.3 Metrics

- **CER** (codepoint, Levenshtein / reference length)
- **AER** (grapheme-cluster Levenshtein) — new
- **WER** (exact string match after NFC)
- Per-writer CER/WER + variance
- Bootstrap 95% CIs over 1,000 resamples of the test set
- Params, peak memory, ms/image at batch 1 and 32

---

## 6. Code architecture

One codebase, two run targets — **identical training code path on Colab and on a local CUDA box.**

The repo root *is* `ocr_hindi/` (`Mtech/code/ocr_hindi/`, its own git repo) — there is no further `code/ocr_hindi/` nesting inside it. `dataset/`, `papers/`, and `plan/` already sit at this root alongside the layout below; everything else here is still to be created.

```
ocr_hindi/                      # ← repo root, git-initialized, no commits yet
├── dataset/                    # IIIT-HW-Hindi_v1 (git-ignored, already present)
├── papers/                     # reference PDF (already present)
├── plan/                       # PLAN.md, plan.html (already present)
├── configs/
│   ├── base.yaml               # shared defaults
│   ├── a0_paper_asis.yaml      # ablation A0 … A8
│   ├── a1_resnet_stride.yaml
│   └── ...
├── src/hindi_htr/
│   ├── data/
│   │   ├── manifest.py         # build train/val/test jsonl, NFC, writer id, aspect
│   │   ├── charset.py          # freeze charset, codepoint + akshara vocabularies
│   │   ├── dataset.py          # LMDB / raw-jpeg dataset
│   │   ├── transforms.py       # elastic, affine, perspective, morphology, noise
│   │   └── bucket_sampler.py   # aspect-ratio bucketing + collate w/ input_lengths
│   ├── models/
│   │   ├── backbones.py        # resnet50_stride21, resnet34, crnn_vgg
│   │   ├── necks.py            # BiLSTM (packed), TransformerEncoder
│   │   ├── heads.py            # CTCHead, AttentionDecoderHead, WriterAdversary
│   │   └── model.py            # assembles from config
│   ├── losses/                 # ctc.py, joint.py (λ-weighted)
│   ├── decode/                 # greedy.py, beam.py, lexicon_trie.py, char_lm.py
│   ├── metrics/                # cer.py, akshara.py, bootstrap.py, per_writer.py
│   ├── engine/                 # trainer.py, evaluator.py, amp.py, checkpoint.py
│   └── utils/                  # seed.py, device.py, logging.py, config.py
├── scripts/
│   ├── prepare_data.py         # run once, CPU — fine on the Mac
│   ├── train.py                # `python -m scripts.train --config configs/a5.yaml`
│   ├── evaluate.py
│   └── export_tables.py        # emits LaTeX tables straight into the paper
├── notebooks/
│   └── colab_train.ipynb       # thin wrapper: mount Drive → pip install → same train.py
├── requirements.txt            # local CUDA
├── requirements-colab.txt      # Colab-pinned
├── .gitignore                  # already present — covers dataset/, checkpoints/, venvs, etc.
└── README.md
```

> Note: an empty leftover `code/` folder currently sits at this repo root from an earlier layout. It's untracked (git doesn't see empty directories) and can simply be deleted or ignored once `src/`, `scripts/`, etc. land — it does nothing and blocks nothing.

### 6.1 Portability rules (Colab ⇄ local GPU)

- `utils/device.py` resolves `cuda → mps → cpu` and gates AMP to CUDA only.
- Every path comes from config (`data_root`, `out_dir`); the Colab notebook only overrides those two.
- `num_workers` auto-derived from `os.cpu_count()`, forced to 2 on Colab.
- Checkpoints written every epoch with full RNG state so a Colab session timeout resumes cleanly — non-negotiable on free Colab's 12-hour limit.
- Zero notebook-only logic. The notebook shells out to `scripts/train.py`; nothing is defined inside it.
- Batch size and gradient accumulation are config-driven so a T4 (16 GB) and a local 4090/A100 run the same experiment at the same effective batch size.

### 6.2 Environment warnings

- **This Mac cannot train.** Intel i7-1068NG7, Intel Iris Plus graphics, 16 GB RAM — no CUDA, and MPS requires Apple Silicon. Use it for data prep, analysis, plotting and writing only.
- **Python 3.14.7 is installed locally and PyTorch publishes no wheels for it.** A **Python 3.11 or 3.12** virtualenv is required for anything importing torch. `scripts/prepare_data.py` is written to run on stdlib + Pillow so the audit stage works anywhere.
- Dataset is 1.8 GB compressed / ~3.5 GB extracted. On Colab, upload the tarball to Drive **once** and extract to local Colab disk each session — reading 95k small JPEGs directly off Drive is pathologically slow. LMDB packing in P0 makes this a single ~3 GB file.

---

## 7. Risks

| Risk | Mitigation |
|---|---|
| Colab session limits kill long runs | resumable checkpoints with RNG state; ≤6 h per run; prefer smaller backbone if needed |
| Joint CTC–Attention is unstable early | warm up with CTC only (λ=1.0), anneal λ to 0.7 after convergence |
| Lexicon decoding looks "too good" and gets challenged in review | always report unconstrained numbers first; closed-vocab is a clearly labelled separate column, plus the held-out-word-type protocol |
| Writer-adversarial branch degrades CER | it is an ablation row, not a hard dependency — keep A6 as the fallback headline model |
| Cannot reproduce the paper's 9.0/18.0 | that is itself a publishable finding, provided A0/A1 are documented rigorously |

---

## 8. Immediate next steps

1. Scaffold `configs/`, `src/hindi_htr/`, `scripts/`, `notebooks/` directly at this repo root (`ocr_hindi/`); remove the empty leftover `code/` folder. Add device abstraction and seeding.
2. Write and run `scripts/prepare_data.py` on this Mac — manifests, NFC, charset freeze, aspect stats, akshara vocabulary, writer table, LMDB pack.
3. Write `train.py` + P1 CRNN config; smoke-test on 2,000 samples on CPU to verify the loop.
4. Move to GPU (Colab or local) and run A0 vs A1 — the G1 evidence.
5. Make an initial commit — the repo currently has no commits, only untracked `.gitignore`, `papers/`, `plan/`.

---

## 9. Open questions for the advisor

- Is a re-implemented CRNN baseline on the matched split acceptable as the comparison anchor, given the paper's own Table 1 is not split-matched?
- Should the open-vocabulary protocol hold out word *types* (harder, more honest) or accept the dataset's closed vocabulary and report both? My recommendation: both, with closed-vocab clearly labelled.
- Target venue — ICDAR / DAS workshop, or an Indic-NLP venue? This affects how much of the write-up goes to the akshara metric versus the architecture.

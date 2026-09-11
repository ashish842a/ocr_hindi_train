#!/usr/bin/env python3
"""
Debug script to diagnose training issues.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import torch
from src.hindi_htr.data import Charset, load_manifest, HindiHTRDataset, collate_fn
from src.hindi_htr.models import build_model
from src.hindi_htr.losses import CTCLoss
from torch.utils.data import DataLoader

# Load config
charset = Charset.load('data_processed/charset.json')
print(f"Charset size: {len(charset)}")
print(f"Blank index: {charset.blank_idx}")
print(f"UNK index: {charset.unk_idx}")
print()

# Load data
train_manifest = load_manifest('data_processed/train_manifest.jsonl')[:100]  # Just 100 samples
print(f"Loaded {len(train_manifest)} training samples")

# Create dataset
dataset = HindiHTRDataset(
    manifest=train_manifest,
    charset=charset,
    data_root='.',
    transform=None,
    target_height=64,
)

# Create dataloader
loader = DataLoader(
    dataset,
    batch_size=4,
    shuffle=False,
    collate_fn=collate_fn,
    num_workers=0,
)

# Get first batch
batch = next(iter(loader))
print(f"\nBatch info:")
print(f"  Images shape: {batch['images'].shape}")
print(f"  Labels shape: {batch['labels'].shape}")
print(f"  Input lengths: {batch['input_lengths']}")
print(f"  Label lengths: {batch['label_lengths']}")
print(f"  Texts: {batch['texts']}")
print()

# Build model
model_config = {
    'backbone_type': 'resnet50',
    'neck_type': 'bilstm',
    'head_type': 'ctc',
    'num_classes': len(charset),
    'backbone_config': {
        'pretrained': False,  # Don't load pretrained for speed
        'fix_stride': True,
        'frozen_stages': 0,
    },
    'neck_config': {
        'hidden_dim': 512,
        'num_layers': 2,
        'dropout': 0.3,
    },
    'head_config': {
        'dropout': 0.3,
    },
}

model = build_model(model_config)
print(f"Model built successfully")

# Test forward pass
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model = model.to(device)
model.eval()

with torch.no_grad():
    images = batch['images'].to(device)
    input_lengths = batch['input_lengths'].to(device)

    outputs = model(images, input_lengths=input_lengths)
    logits = outputs['ctc_logits']

    print(f"\nModel outputs:")
    print(f"  CTC logits shape: {logits.shape}")
    print(f"  Expected: [T={logits.shape[0]}, B={logits.shape[1]}, C={logits.shape[2]}]")
    print(f"  Input lengths (original): {batch['input_lengths'].tolist()}")
    print(f"  Input lengths (clamped): {torch.clamp(input_lengths, max=logits.size(0)).tolist()}")
    print()

# Test CTC loss
criterion = CTCLoss(blank_idx=charset.blank_idx)

labels = batch['labels'].to(device)
label_lengths = batch['label_lengths'].to(device)
ctc_input_lengths = torch.clamp(input_lengths, max=logits.size(0))

try:
    loss = criterion(
        logits=logits,
        targets=labels,
        input_lengths=ctc_input_lengths,
        target_lengths=label_lengths,
    )
    print(f"CTC Loss computed successfully: {loss.item():.4f}")
    print()
except Exception as e:
    print(f"ERROR computing CTC loss: {e}")
    print()

# Decode predictions
log_probs = torch.log_softmax(logits, dim=2)
_, preds = log_probs.max(dim=2)  # [T, B]

print("Sample predictions (greedy decoding):")
for i in range(min(4, batch['images'].size(0))):
    pred_seq = preds[:, i].cpu().tolist()
    decoded = charset.decode(pred_seq, remove_duplicates=True)
    print(f"  Sample {i}:")
    print(f"    Ground truth: {batch['texts'][i]}")
    print(f"    Prediction:   {decoded}")
    print(f"    Label length: {batch['label_lengths'][i]}, Seq length: {ctc_input_lengths[i]}")
print()

# Check if input_lengths >= label_lengths (CTC requirement)
print("Checking CTC requirements:")
for i in range(len(batch['texts'])):
    inp_len = ctc_input_lengths[i].item()
    lab_len = batch['label_lengths'][i]
    status = "✓" if inp_len >= lab_len else "✗ VIOLATION"
    print(f"  Sample {i}: input_len={inp_len}, label_len={lab_len} {status}")

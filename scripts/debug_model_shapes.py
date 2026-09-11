#!/usr/bin/env python3
"""
Debug script to trace shapes through the model.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import torch
from src.hindi_htr.data import Charset, load_manifest, HindiHTRDataset, collate_fn
from src.hindi_htr.models.backbones import ResNetBackbone
from src.hindi_htr.models.necks import BiLSTMNeck
from src.hindi_htr.models.heads import CTCHead
from torch.utils.data import DataLoader

# Load data
train_manifest = load_manifest('data_processed/train_manifest.jsonl')[:10]
charset = Charset.load('data_processed/charset.json')

dataset = HindiHTRDataset(
    manifest=train_manifest,
    charset=charset,
    data_root='.',
    transform=None,
    target_height=64,
)

loader = DataLoader(dataset, batch_size=2, shuffle=False, collate_fn=collate_fn, num_workers=0)
batch = next(iter(loader))

print("="*80)
print("INPUT")
print("="*80)
print(f"Images shape: {batch['images'].shape}")
print(f"Input lengths: {batch['input_lengths']}")
print(f"Texts: {batch['texts']}")
print()

# Test each component separately
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
images = batch['images'].to(device)
input_lengths = batch['input_lengths'].to(device)

# Backbone
print("="*80)
print("BACKBONE (ResNet50)")
print("="*80)
backbone = ResNetBackbone(pretrained=False, fix_stride=True, frozen_stages=0).to(device)
backbone.eval()

with torch.no_grad():
    features = backbone(images)
    print(f"Input:  {images.shape}")
    print(f"Output: {features.shape}")
    print(f"Expected: [B={images.size(0)}, T≈{images.size(3)//8}, C=2048]")
    print()

# Neck
print("="*80)
print("NECK (BiLSTM)")
print("="*80)
neck = BiLSTMNeck(input_dim=2048, hidden_dim=512, num_layers=2, dropout=0.3).to(device)
neck.eval()

# Adjust lengths for backbone downsampling
adjusted_lengths = (input_lengths / 8).long()
adjusted_lengths = torch.clamp(adjusted_lengths, max=features.size(1))
print(f"Original lengths: {input_lengths}")
print(f"Adjusted lengths: {adjusted_lengths}")
print()

with torch.no_grad():
    encoded = neck(features, lengths=adjusted_lengths)
    print(f"Input:  {features.shape}")
    print(f"Output: {encoded.shape}")
    print(f"Expected: [B={features.size(0)}, T={features.size(1)}, C=1024]")
    print()

# Head
print("="*80)
print("HEAD (CTC)")
print("="*80)
head = CTCHead(input_dim=1024, num_classes=102, dropout=0.3).to(device)
head.eval()

with torch.no_grad():
    logits = head(encoded)
    print(f"Input:  {encoded.shape}")
    print(f"Output: {logits.shape}")
    print(f"Expected: [B={encoded.size(0)}, T={encoded.size(1)}, C=102]")
    print()

print("="*80)
print("SUMMARY")
print("="*80)
print(f"Image width: {images.size(3)}")
print(f"Expected sequence length: {images.size(3) // 8}")
print(f"Actual sequence length: {logits.size(1)}")
print(f"Label lengths: {batch['label_lengths']}")
print()

if logits.size(1) < images.size(3) // 8:
    print("⚠️  WARNING: Sequence length is shorter than expected!")
    print(f"   Loss: {images.size(3) // 8 - logits.size(1)} time steps")
else:
    print("✓ Sequence length is correct")

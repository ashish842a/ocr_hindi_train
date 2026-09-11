"""Aspect-ratio based bucket sampler for efficient batching."""

import torch
from torch.utils.data import Sampler
from typing import List, Dict, Iterator
import numpy as np
import random


class AspectRatioBucketSampler(Sampler):
    """
    Sampler that groups samples by aspect ratio into buckets.

    Reduces padding waste for variable-width images.
    """

    def __init__(
        self,
        manifest: List[Dict],
        batch_size: int,
        num_buckets: int = 10,
        shuffle: bool = True,
        drop_last: bool = False,
    ):
        """
        Initialize bucket sampler.

        Args:
            manifest: Dataset manifest with 'aspect_ratio' field
            batch_size: Batch size
            num_buckets: Number of aspect ratio buckets
            shuffle: Whether to shuffle buckets and batches
            drop_last: Whether to drop incomplete last batch
        """
        self.manifest = manifest
        self.batch_size = batch_size
        self.num_buckets = num_buckets
        self.shuffle = shuffle
        self.drop_last = drop_last

        # Get aspect ratios
        aspect_ratios = [entry['aspect_ratio'] for entry in manifest]

        # Create buckets
        self.buckets = self._create_buckets(aspect_ratios)

    def _create_buckets(self, aspect_ratios: List[float]) -> List[List[int]]:
        """
        Assign samples to buckets based on aspect ratio.

        Args:
            aspect_ratios: List of aspect ratios

        Returns:
            List of buckets, each containing sample indices
        """
        # Compute bucket boundaries
        sorted_aspects = sorted(aspect_ratios)
        bucket_boundaries = []

        for i in range(self.num_buckets):
            idx = int((i + 1) * len(sorted_aspects) / self.num_buckets) - 1
            bucket_boundaries.append(sorted_aspects[idx])

        # Assign samples to buckets
        buckets = [[] for _ in range(self.num_buckets)]

        for idx, aspect in enumerate(aspect_ratios):
            # Find bucket
            bucket_idx = 0
            for boundary in bucket_boundaries:
                if aspect <= boundary:
                    break
                bucket_idx += 1
                if bucket_idx >= self.num_buckets:
                    bucket_idx = self.num_buckets - 1
                    break

            buckets[bucket_idx].append(idx)

        return buckets

    def __iter__(self) -> Iterator[List[int]]:
        """Generate batches."""
        # Shuffle buckets
        if self.shuffle:
            buckets = [bucket.copy() for bucket in self.buckets]
            for bucket in buckets:
                random.shuffle(bucket)
            random.shuffle(buckets)
        else:
            buckets = self.buckets

        # Generate batches from buckets
        batches = []
        for bucket in buckets:
            for i in range(0, len(bucket), self.batch_size):
                batch = bucket[i:i + self.batch_size]

                if len(batch) == self.batch_size or not self.drop_last:
                    batches.append(batch)

        # Shuffle batches
        if self.shuffle:
            random.shuffle(batches)

        for batch in batches:
            yield batch

    def __len__(self) -> int:
        """Return number of batches."""
        total_batches = 0
        for bucket in self.buckets:
            bucket_batches = len(bucket) // self.batch_size
            if not self.drop_last and len(bucket) % self.batch_size != 0:
                bucket_batches += 1
            total_batches += bucket_batches
        return total_batches


def collate_fn(batch: List[Dict]) -> Dict:
    """
    Collate function with right-padding for variable-width images.

    Args:
        batch: List of samples from dataset

    Returns:
        Batched dictionary with padded images and labels
    """
    # Find max dimensions
    max_width = max(sample['width'] for sample in batch)
    max_label_length = max(sample['length'] for sample in batch)

    # Prepare tensors
    batch_size = len(batch)
    images = []
    labels = []
    label_lengths = []
    input_lengths = []
    texts = []

    for sample in batch:
        img = sample['image']  # [1, H, W]
        h, w = img.shape[1], img.shape[2]

        # Pad image to max_width (right padding)
        if w < max_width:
            pad_width = max_width - w
            img = torch.nn.functional.pad(img, (0, pad_width), value=0)

        images.append(img)

        # Pad label
        label = sample['label']
        if len(label) < max_label_length:
            # Pad with -1 (will be ignored by CTC loss via target_lengths)
            # Do NOT pad with 0 (blank token) as it can confuse training
            label = torch.nn.functional.pad(
                label,
                (0, max_label_length - len(label)),
                value=-1
            )

        labels.append(label)
        label_lengths.append(sample['length'])

        # Compute input length (CTC requires frame count)
        # ResNet backbone downsamples by factor of 8 (stride 8)
        input_lengths.append(w // 8)

        texts.append(sample['text'])

    # Stack tensors
    images = torch.stack(images, dim=0)  # [B, 1, H, W]
    labels = torch.stack(labels, dim=0)  # [B, max_label_length]
    label_lengths = torch.tensor(label_lengths, dtype=torch.long)
    input_lengths = torch.tensor(input_lengths, dtype=torch.long)

    return {
        'images': images,
        'labels': labels,
        'label_lengths': label_lengths,
        'input_lengths': input_lengths,
        'texts': texts,
    }

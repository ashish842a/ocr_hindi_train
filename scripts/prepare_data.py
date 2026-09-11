#!/usr/bin/env python3
"""
Data preparation script (Phase P0).

Builds manifests, creates charset, computes statistics.
Can run on CPU/Mac - no GPU required.
"""

import argparse
import json
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.hindi_htr.data import build_manifest, load_manifest, build_charset


def main():
    parser = argparse.ArgumentParser(description='Prepare IIIT-HW-Hindi dataset')
    parser.add_argument(
        '--data-root',
        type=str,
        required=True,
        help='Root directory of IIIT-HW-Hindi dataset'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='data_processed',
        help='Output directory for manifests and charset'
    )
    parser.add_argument(
        '--min-char-freq',
        type=int,
        default=50,
        help='Minimum character frequency for charset'
    )
    parser.add_argument(
        '--normalize',
        action='store_true',
        default=True,
        help='Apply NFC normalization'
    )

    args = parser.parse_args()

    data_root = Path(args.data_root)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 80)
    print("IIIT-HW-Hindi Dataset Preparation")
    print("=" * 80)

    # Build manifests for each split
    manifests = {}
    for split in ['train', 'val', 'test']:
        print(f"\n{'='*80}")
        print(f"Processing {split.upper()} split")
        print('=' * 80)

        manifest_path = output_dir / f'{split}_manifest.jsonl'

        manifest = build_manifest(
            data_root=str(data_root),
            split=split,
            output_path=str(manifest_path),
            normalize=args.normalize,
            verbose=True,
        )

        manifests[split] = manifest

    # Build charset from training data
    print(f"\n{'='*80}")
    print("Building character set")
    print('=' * 80)

    train_labels = [entry['text'] for entry in manifests['train']]

    charset = build_charset(
        labels=train_labels,
        min_freq=args.min_char_freq,
        normalize=args.normalize,
        use_blank=True,
        use_unk=True,
    )

    # Save charset
    charset_path = output_dir / 'charset.json'
    charset.save(str(charset_path))
    print(f"\nCharset saved to: {charset_path}")
    print(f"Vocabulary size: {len(charset)}")

    # Compute and save statistics
    print(f"\n{'='*80}")
    print("Dataset Statistics")
    print('=' * 80)

    stats = {}
    for split, manifest in manifests.items():
        from collections import Counter

        writer_counts = Counter(e['writer_id'] for e in manifest)
        text_lengths = [len(e['text']) for e in manifest]
        unique_words = len(set(e['text'] for e in manifest))

        stats[split] = {
            'total_samples': len(manifest),
            'unique_writers': len(writer_counts),
            'writers': dict(writer_counts),
            'unique_word_types': unique_words,
            'text_length_min': min(text_lengths),
            'text_length_max': max(text_lengths),
            'text_length_mean': sum(text_lengths) / len(text_lengths),
        }

        print(f"\n{split.upper()}:")
        print(f"  Samples: {stats[split]['total_samples']}")
        print(f"  Writers: {stats[split]['unique_writers']} ({list(writer_counts.keys())})")
        print(f"  Unique words: {stats[split]['unique_word_types']}")
        print(f"  Text length: {stats[split]['text_length_min']} - {stats[split]['text_length_max']} "
              f"(mean: {stats[split]['text_length_mean']:.1f})")

    # Save statistics
    stats_path = output_dir / 'statistics.json'
    with open(stats_path, 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

    print(f"\nStatistics saved to: {stats_path}")

    # Compute cross-split vocabulary coverage
    print(f"\n{'='*80}")
    print("Vocabulary Coverage")
    print('=' * 80)

    train_vocab = set(e['text'] for e in manifests['train'])
    val_vocab = set(e['text'] for e in manifests['val'])
    test_vocab = set(e['text'] for e in manifests['test'])

    val_unseen = val_vocab - train_vocab
    test_unseen = test_vocab - train_vocab

    print(f"\nValidation:")
    print(f"  Total word types: {len(val_vocab)}")
    print(f"  Unseen in training: {len(val_unseen)} ({100*len(val_unseen)/len(val_vocab):.2f}%)")

    print(f"\nTest:")
    print(f"  Total word types: {len(test_vocab)}")
    print(f"  Unseen in training: {len(test_unseen)} ({100*len(test_unseen)/len(test_vocab):.2f}%)")

    if len(val_unseen) == 0 and len(test_unseen) == 0:
        print("\n⚠️  WARNING: This is a CLOSED-VOCABULARY benchmark!")
        print("   All validation and test words appear in training.")
        print("   WER results should be reported with this caveat.")

    print(f"\n{'='*80}")
    print("Data preparation complete!")
    print('=' * 80)
    print(f"\nOutputs saved to: {output_dir.absolute()}")


if __name__ == '__main__':
    main()

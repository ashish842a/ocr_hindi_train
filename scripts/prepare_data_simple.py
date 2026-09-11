#!/usr/bin/env python3
"""
Simple data preparation script for IIIT-HW-Hindi dataset
Works with the dataset structure where annotations are in .txt files
"""
import argparse
import json
from pathlib import Path
from collections import Counter
from unicodedata import normalize as unicode_normalize
from PIL import Image

def build_manifest_from_txt(txt_path, data_root, normalize=False):
    """Build manifest from .txt annotation file"""
    manifest = []
    missing_files = []

    data_root = Path(data_root)

    with open(txt_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue

            parts = line.split()
            if len(parts) < 2:
                print(f"Warning: Skipping malformed line {line_num}: {line}")
                continue

            # Image path is first part, text is everything after
            img_path = parts[0]
            text = ' '.join(parts[1:])

            # Apply NFC normalization if requested
            if normalize:
                text = unicode_normalize('NFC', text)

            # Full path to image
            full_img_path = data_root / img_path

            # Check if file exists
            if not full_img_path.exists():
                missing_files.append(str(full_img_path))
                continue

            # Load image to get dimensions and calculate aspect ratio
            try:
                with Image.open(full_img_path) as img:
                    width, height = img.size
                    aspect_ratio = width / height
            except Exception as e:
                print(f"Warning: Could not load image {full_img_path}: {e}")
                continue

            manifest.append({
                'image_path': str(full_img_path),
                'text': text,
                'width': width,
                'height': height,
                'aspect_ratio': aspect_ratio
            })

    if missing_files:
        print(f"Warning: {len(missing_files)} image files not found")
        if len(missing_files) <= 10:
            for f in missing_files:
                print(f"  - {f}")
        else:
            print(f"  First 10:")
            for f in missing_files[:10]:
                print(f"    - {f}")

    return manifest

def build_charset(manifests, min_freq=1):
    """Build character set from manifests"""
    char_counter = Counter()

    for manifest in manifests:
        for entry in manifest:
            char_counter.update(entry['text'])

    # Filter by minimum frequency
    charset = sorted([char for char, freq in char_counter.items() if freq >= min_freq])

    return charset, char_counter

def save_manifest(manifest, output_path):
    """Save manifest as JSONL"""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        for entry in manifest:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')

def print_stats(split_name, manifest, char_counter=None):
    """Print statistics for a split"""
    print(f"\n{split_name.upper()} Statistics:")
    print(f"  Total samples: {len(manifest)}")

    if manifest:
        text_lengths = [len(entry['text']) for entry in manifest]
        print(f"  Text length: min={min(text_lengths)}, max={max(text_lengths)}, avg={sum(text_lengths)/len(text_lengths):.1f}")

    if char_counter:
        print(f"  Unique characters: {len(char_counter)}")
        print(f"  Total characters: {sum(char_counter.values())}")

def main():
    parser = argparse.ArgumentParser(description='Prepare IIIT-HW-Hindi dataset')
    parser.add_argument('--data-root', type=str, default='dataset',
                        help='Root directory containing the dataset')
    parser.add_argument('--output-dir', type=str, default='data_processed',
                        help='Output directory for processed data')
    parser.add_argument('--min-char-freq', type=int, default=1,
                        help='Minimum character frequency to include in charset')
    parser.add_argument('--normalize', action='store_true',
                        help='Apply NFC Unicode normalization to text')

    args = parser.parse_args()

    print("=" * 80)
    print("IIIT-HW-Hindi Dataset Preparation (Simple)")
    print("=" * 80)

    data_root = Path(args.data_root)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Process each split
    manifests = {}
    for split in ['train', 'val', 'test']:
        print(f"\n{'=' * 80}")
        print(f"Processing {split.upper()} split")
        print("=" * 80)

        txt_file = data_root / f"{split}.txt"

        if not txt_file.exists():
            print(f"Warning: {txt_file} not found, skipping...")
            continue

        manifest = build_manifest_from_txt(
            txt_file,
            data_root,
            normalize=args.normalize
        )

        manifests[split] = manifest

        # Save manifest
        output_path = output_dir / f"{split}_manifest.jsonl"
        save_manifest(manifest, output_path)
        print(f"Saved manifest to: {output_path}")

        # Print stats
        print_stats(split, manifest)

    # Build and save charset
    if manifests:
        print(f"\n{'=' * 80}")
        print("Building character set")
        print("=" * 80)

        all_manifests = list(manifests.values())
        charset, char_counter = build_charset(all_manifests, args.min_char_freq)

        # Save as JSON (required format for training)
        charset_json_path = output_dir / "charset.json"
        charset_data = {
            'characters': charset,
            'use_blank': True,
            'use_unk': True,
            'min_freq': args.min_char_freq,
        }
        with open(charset_json_path, 'w', encoding='utf-8') as f:
            json.dump(charset_data, f, ensure_ascii=False, indent=2)

        # Also save as TXT for easy viewing
        charset_txt_path = output_dir / "charset.txt"
        with open(charset_txt_path, 'w', encoding='utf-8') as f:
            for char in charset:
                f.write(char + '\n')

        print(f"Charset saved to: {charset_json_path}")
        print(f"Charset (text) saved to: {charset_txt_path}")
        print(f"Total unique characters: {len(charset)}")
        print(f"Minimum character frequency: {args.min_char_freq}")

        # Show most common characters
        print(f"\nTop 20 most common characters:")
        for char, freq in char_counter.most_common(20):
            print(f"  '{char}': {freq}")

    print(f"\n{'=' * 80}")
    print("Dataset preparation complete!")
    print("=" * 80)
    print(f"\nOutput directory: {output_dir}")
    print(f"Files created:")
    for split in manifests.keys():
        print(f"  - {split}_manifest.jsonl ({len(manifests[split])} samples)")
    print(f"  - charset.json ({len(charset)} characters)")
    print(f"  - charset.txt ({len(charset)} characters)")

if __name__ == '__main__':
    main()

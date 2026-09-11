"""Dataset manifest building and loading.

Builds JSONL manifests with NFC normalization, writer IDs, and image metadata.
"""

import json
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from PIL import Image
from tqdm import tqdm

from .charset import normalize_text


def build_manifest(
    data_root: str,
    split: str,
    output_path: str,
    normalize: bool = True,
    verbose: bool = True,
) -> List[Dict]:
    """
    Build manifest from IIIT-HW-Hindi dataset.

    Expected structure:
        data_root/
            writer_{id}/
                page_{id}/
                    {word_id}.png
                    words.txt  (word_id<tab>text)

    Args:
        data_root: Root directory of the dataset
        split: Split name (train/val/test)
        output_path: Path to save manifest JSONL
        normalize: Whether to apply NFC normalization
        verbose: Whether to show progress

    Returns:
        List of manifest entries
    """
    data_root = Path(data_root)
    split_dir = data_root / split

    if not split_dir.exists():
        raise ValueError(f"Split directory not found: {split_dir}")

    manifest = []
    missing_files = []

    # Iterate through writers
    writer_dirs = sorted(split_dir.glob("writer_*"))

    if verbose:
        print(f"Building manifest for split: {split}")
        writer_dirs = tqdm(writer_dirs, desc="Writers")

    for writer_dir in writer_dirs:
        writer_id = writer_dir.name.split('_')[1]

        # Iterate through pages
        for page_dir in sorted(writer_dir.glob("page_*")):
            page_id = page_dir.name.split('_')[1]

            # Read words.txt
            words_file = page_dir / "words.txt"
            if not words_file.exists():
                if verbose:
                    print(f"Warning: words.txt not found in {page_dir}")
                continue

            with open(words_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue

                    parts = line.split('\t')
                    if len(parts) != 2:
                        continue

                    word_id, text = parts

                    # Image path
                    img_path = page_dir / f"{word_id}.png"
                    if not img_path.exists():
                        missing_files.append(str(img_path))
                        continue

                    # Get image dimensions
                    try:
                        with Image.open(img_path) as img:
                            width, height = img.size
                    except Exception as e:
                        if verbose:
                            print(f"Error reading {img_path}: {e}")
                        continue

                    # Normalize text
                    if normalize:
                        original_text = text
                        text = normalize_text(text)
                    else:
                        original_text = text

                    # Build entry
                    entry = {
                        'image_path': str(img_path.relative_to(data_root)),
                        'text': text,
                        'writer_id': writer_id,
                        'page_id': page_id,
                        'word_id': word_id,
                        'width': width,
                        'height': height,
                        'aspect_ratio': width / height,
                    }

                    if normalize and original_text != text:
                        entry['original_text'] = original_text

                    manifest.append(entry)

    if verbose:
        print(f"\nManifest statistics for {split}:")
        print(f"  Total entries: {len(manifest)}")
        print(f"  Unique writers: {len(set(e['writer_id'] for e in manifest))}")
        print(f"  Missing files: {len(missing_files)}")

        if manifest:
            widths = [e['width'] for e in manifest]
            heights = [e['height'] for e in manifest]
            aspects = [e['aspect_ratio'] for e in manifest]

            print(f"  Width: min={min(widths)} p50={sorted(widths)[len(widths)//2]} max={max(widths)}")
            print(f"  Height: min={min(heights)} p50={sorted(heights)[len(heights)//2]} max={max(heights)}")
            print(f"  Aspect ratio: min={min(aspects):.2f} p50={sorted(aspects)[len(aspects)//2]:.2f} max={max(aspects):.2f}")

    # Save manifest
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        for entry in manifest:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')

    if verbose:
        print(f"\nManifest saved to: {output_path}")

    return manifest


def load_manifest(manifest_path: str) -> List[Dict]:
    """
    Load manifest from JSONL file.

    Args:
        manifest_path: Path to manifest file

    Returns:
        List of manifest entries
    """
    manifest = []

    with open(manifest_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                manifest.append(json.loads(line))

    return manifest


def get_split_statistics(manifest: List[Dict]) -> Dict:
    """
    Compute statistics from manifest.

    Args:
        manifest: List of manifest entries

    Returns:
        Dictionary of statistics
    """
    if not manifest:
        return {}

    from collections import Counter

    writer_counts = Counter(e['writer_id'] for e in manifest)
    text_lengths = [len(e['text']) for e in manifest]
    unique_words = len(set(e['text'] for e in manifest))

    return {
        'total_samples': len(manifest),
        'unique_writers': len(writer_counts),
        'writers': dict(writer_counts),
        'unique_word_types': unique_words,
        'text_length_min': min(text_lengths),
        'text_length_max': max(text_lengths),
        'text_length_mean': sum(text_lengths) / len(text_lengths),
    }

"""Character set and vocabulary management.

Handles both codepoint-level and akshara (grapheme cluster) vocabularies.
"""

import json
import unicodedata
from pathlib import Path
from typing import List, Dict, Optional, Set
from collections import Counter


class Charset:
    """Character set with encoding/decoding capabilities."""

    # Special tokens
    BLANK = '<blank>'  # CTC blank
    UNK = '<unk>'      # Unknown character

    def __init__(
        self,
        characters: List[str],
        use_blank: bool = True,
        use_unk: bool = True,
        min_freq: int = 1
    ):
        """
        Initialize charset.

        Args:
            characters: List of characters in the vocabulary
            use_blank: Whether to include CTC blank token
            use_unk: Whether to include unknown token
            min_freq: Minimum frequency threshold (for filtering)
        """
        self.use_blank = use_blank
        self.use_unk = use_unk
        self.min_freq = min_freq

        # Build vocabulary
        vocab = []
        if use_blank:
            vocab.append(self.BLANK)
        if use_unk:
            vocab.append(self.UNK)

        vocab.extend(characters)

        self.char2idx = {ch: idx for idx, ch in enumerate(vocab)}
        self.idx2char = {idx: ch for ch, idx in self.char2idx.items()}

        self.blank_idx = self.char2idx[self.BLANK] if use_blank else None
        self.unk_idx = self.char2idx[self.UNK] if use_unk else None

    def __len__(self) -> int:
        """Return vocabulary size."""
        return len(self.char2idx)

    def encode(self, text: str) -> List[int]:
        """
        Encode text to indices.

        Args:
            text: Input text

        Returns:
            List of character indices
        """
        indices = []
        for ch in text:
            if ch in self.char2idx:
                indices.append(self.char2idx[ch])
            elif self.use_unk:
                indices.append(self.unk_idx)
            # else: skip unknown characters

        return indices

    def decode(self, indices: List[int], remove_duplicates: bool = True) -> str:
        """
        Decode indices to text.

        Args:
            indices: List of character indices
            remove_duplicates: Whether to remove duplicate consecutive characters (CTC)

        Returns:
            Decoded text
        """
        chars = []
        prev_idx = None

        for idx in indices:
            # Skip blank
            if self.use_blank and idx == self.blank_idx:
                prev_idx = None
                continue

            # Skip duplicates if requested
            if remove_duplicates and idx == prev_idx:
                continue

            if idx in self.idx2char:
                chars.append(self.idx2char[idx])

            prev_idx = idx

        return ''.join(chars)

    def save(self, path: str) -> None:
        """Save charset to JSON."""
        data = {
            'characters': [self.idx2char[i] for i in range(len(self))],
            'use_blank': self.use_blank,
            'use_unk': self.use_unk,
            'min_freq': self.min_freq,
        }

        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    @classmethod
    def load(cls, path: str) -> 'Charset':
        """Load charset from JSON."""
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Remove special tokens from characters list
        characters = [ch for ch in data['characters'] if ch not in [cls.BLANK, cls.UNK]]

        return cls(
            characters=characters,
            use_blank=data.get('use_blank', True),
            use_unk=data.get('use_unk', True),
            min_freq=data.get('min_freq', 1),
        )


def normalize_text(text: str) -> str:
    """
    Normalize text using Unicode NFC normalization.

    Args:
        text: Input text

    Returns:
        NFC-normalized text
    """
    return unicodedata.normalize('NFC', text)


def build_charset(
    labels: List[str],
    min_freq: int = 50,
    normalize: bool = True,
    use_blank: bool = True,
    use_unk: bool = True,
) -> Charset:
    """
    Build charset from labels.

    Args:
        labels: List of text labels
        min_freq: Minimum character frequency (characters below this become <unk>)
        normalize: Whether to apply NFC normalization
        use_blank: Whether to include CTC blank token
        use_unk: Whether to include unknown token

    Returns:
        Charset instance
    """
    # Count characters
    char_counter = Counter()

    for label in labels:
        if normalize:
            label = normalize_text(label)

        for ch in label:
            char_counter[ch] += 1

    # Filter by frequency
    characters = sorted([
        ch for ch, count in char_counter.items()
        if count >= min_freq
    ])

    print(f"Total unique characters: {len(char_counter)}")
    print(f"Characters with freq >= {min_freq}: {len(characters)}")

    if len(char_counter) > len(characters):
        rare_chars = [ch for ch, count in char_counter.items() if count < min_freq]
        rare_count = sum(char_counter[ch] for ch in rare_chars)
        total_count = sum(char_counter.values())
        print(f"Rare characters (< {min_freq} occurrences): {len(rare_chars)}")
        print(f"Rare character tokens: {rare_count} ({100 * rare_count / total_count:.2f}%)")

    return Charset(
        characters=characters,
        use_blank=use_blank,
        use_unk=use_unk,
        min_freq=min_freq,
    )


def extract_akshara_units(text: str) -> List[str]:
    """
    Extract akshara (grapheme cluster) units from Devanagari text.

    A simple implementation that groups base characters with their combining marks.

    Args:
        text: Input Devanagari text

    Returns:
        List of akshara units
    """
    import unicodedata

    aksharas = []
    current = []

    for ch in text:
        cat = unicodedata.category(ch)

        # Combining marks (Mn, Mc) attach to the previous base
        if cat in ('Mn', 'Mc'):
            current.append(ch)
        else:
            # New base character
            if current:
                aksharas.append(''.join(current))
            current = [ch]

    if current:
        aksharas.append(''.join(current))

    return aksharas

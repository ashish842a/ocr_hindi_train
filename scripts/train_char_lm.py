#!/usr/bin/env python3
"""
Train character-level n-gram language model for Hindi.

Usage:
    python scripts/train_char_lm.py --n 5 --output models/char_5gram_lm.pkl
"""

import argparse
import json
import pickle
from pathlib import Path
from collections import defaultdict, Counter
import numpy as np


class CharNGramLM:
    """Character-level n-gram language model."""

    def __init__(self, n: int = 5):
        """
        Initialize n-gram language model.

        Args:
            n: N-gram order (default: 5)
        """
        self.n = n
        self.ngrams = defaultdict(Counter)
        self.vocab = set()
        self.num_texts = 0

    def train(self, texts: list):
        """
        Train language model on texts.

        Args:
            texts: List of text strings
        """
        print(f"Training {self.n}-gram language model on {len(texts)} samples...")

        for i, text in enumerate(texts):
            if i % 10000 == 0:
                print(f"  Processed {i}/{len(texts)} texts...")

            # Add start/end markers
            text = '<' * (self.n - 1) + text + '>'
            self.vocab.update(text)

            # Extract n-grams
            for j in range(len(text) - self.n + 1):
                context = text[j:j + self.n - 1]
                char = text[j + self.n - 1]
                self.ngrams[context][char] += 1

        self.num_texts = len(texts)

        # Normalize to probabilities with Laplace smoothing
        print("Normalizing to probabilities...")
        vocab_size = len(self.vocab)

        for context in self.ngrams:
            total = sum(self.ngrams[context].values()) + vocab_size  # Laplace smoothing
            for char in self.vocab:
                count = self.ngrams[context].get(char, 0) + 1  # Add-1 smoothing
                self.ngrams[context][char] = count / total

        print(f"✓ Training complete!")
        print(f"  Vocabulary size: {len(self.vocab)}")
        print(f"  Unique {self.n}-grams: {len(self.ngrams)}")

    def score(self, text: str) -> float:
        """
        Compute log probability of text.

        Args:
            text: Input text

        Returns:
            Log probability
        """
        text = '<' * (self.n - 1) + text + '>'
        log_prob = 0.0

        for i in range(len(text) - self.n + 1):
            context = text[i:i + self.n - 1]
            char = text[i + self.n - 1]

            if context in self.ngrams and char in self.ngrams[context]:
                prob = self.ngrams[context][char]
            else:
                prob = 1.0 / len(self.vocab)  # Fallback to uniform

            log_prob += np.log(max(prob, 1e-10))  # Avoid log(0)

        return log_prob

    def perplexity(self, text: str) -> float:
        """Compute perplexity of text."""
        log_prob = self.score(text)
        return np.exp(-log_prob / len(text))

    def save(self, path: str):
        """Save language model to file."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, 'wb') as f:
            pickle.dump({
                'n': self.n,
                'ngrams': dict(self.ngrams),  # Convert defaultdict
                'vocab': self.vocab,
                'num_texts': self.num_texts,
            }, f)

        print(f"✓ Saved language model to: {path}")

    @classmethod
    def load(cls, path: str):
        """Load language model from file."""
        with open(path, 'rb') as f:
            data = pickle.load(f)

        lm = cls(n=data['n'])
        lm.ngrams = defaultdict(Counter, data['ngrams'])
        lm.vocab = data['vocab']
        lm.num_texts = data['num_texts']

        return lm


def main():
    parser = argparse.ArgumentParser(description='Train character n-gram language model')
    parser.add_argument('--n', type=int, default=5, help='N-gram order')
    parser.add_argument('--train-manifest', type=str, default='data_processed/train_manifest.jsonl',
                        help='Training manifest')
    parser.add_argument('--output', type=str, default='models/char_5gram_lm.pkl',
                        help='Output path for language model')
    parser.add_argument('--test', action='store_true', help='Test LM after training')

    args = parser.parse_args()

    # Load training texts
    print(f"Loading training texts from: {args.train_manifest}")
    texts = []
    with open(args.train_manifest, encoding='utf-8') as f:
        for line in f:
            data = json.loads(line.strip())
            texts.append(data['text'])

    print(f"Loaded {len(texts)} training samples")

    # Train language model
    lm = CharNGramLM(n=args.n)
    lm.train(texts)

    # Save
    lm.save(args.output)

    # Test
    if args.test:
        print("\n" + "="*80)
        print("TESTING LANGUAGE MODEL")
        print("="*80)

        # Test on sample texts
        test_samples = [
            "नमस्ते",  # Common Hindi word
            "प्रतिभावान",  # Complex word
            "xyzabc",  # Non-Hindi (should score low)
        ]

        for text in test_samples:
            score = lm.score(text)
            perplexity = lm.perplexity(text)
            print(f"Text: {text:20s} | Log Prob: {score:10.2f} | Perplexity: {perplexity:8.2f}")


if __name__ == '__main__':
    main()

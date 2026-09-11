"""Greedy decoding for CTC."""

import torch
from typing import List


def greedy_decode(
    logits: torch.Tensor,
    charset,
    blank_idx: int = 0,
) -> List[str]:
    """
    Greedy CTC decoding.

    Args:
        logits: Model outputs [B, T, num_classes]
        charset: Charset for decoding
        blank_idx: Blank token index

    Returns:
        List of decoded strings
    """
    # Get best path
    preds = torch.argmax(logits, dim=-1)  # [B, T]

    results = []
    for pred in preds:
        # Remove blanks and collapse repeats
        decoded = charset.decode(pred.tolist(), remove_duplicates=True)
        results.append(decoded)

    return results

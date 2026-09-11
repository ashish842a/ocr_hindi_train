"""Character Error Rate and Word Error Rate metrics."""

import editdistance
from typing import List


def compute_cer(predictions: List[str], references: List[str]) -> float:
    """
    Compute Character Error Rate.

    CER = (substitutions + insertions + deletions) / total characters

    Args:
        predictions: List of predicted texts
        references: List of reference texts

    Returns:
        CER value (0 to 1+)
    """
    total_chars = 0
    total_distance = 0

    for pred, ref in zip(predictions, references):
        distance = editdistance.eval(pred, ref)
        total_distance += distance
        total_chars += len(ref)

    if total_chars == 0:
        return 0.0

    return total_distance / total_chars


def compute_wer(predictions: List[str], references: List[str]) -> float:
    """
    Compute Word Error Rate.

    WER = (substitutions + insertions + deletions) / total words

    Args:
        predictions: List of predicted texts
        references: List of reference texts

    Returns:
        WER value (0 to 1+)
    """
    total_words = 0
    total_distance = 0

    for pred, ref in zip(predictions, references):
        # Split into words
        pred_words = pred.split()
        ref_words = ref.split()

        distance = editdistance.eval(pred_words, ref_words)
        total_distance += distance
        total_words += len(ref_words)

    if total_words == 0:
        return 0.0

    return total_distance / total_words


def compute_akshara_error_rate(
    predictions: List[str],
    references: List[str],
    akshara_tokenizer,
) -> float:
    """
    Compute Akshara (grapheme cluster) Error Rate.

    Args:
        predictions: List of predicted texts
        references: List of reference texts
        akshara_tokenizer: Function to tokenize text into aksharas

    Returns:
        AER value (0 to 1+)
    """
    total_aksharas = 0
    total_distance = 0

    for pred, ref in zip(predictions, references):
        pred_aksharas = akshara_tokenizer(pred)
        ref_aksharas = akshara_tokenizer(ref)

        distance = editdistance.eval(pred_aksharas, ref_aksharas)
        total_distance += distance
        total_aksharas += len(ref_aksharas)

    if total_aksharas == 0:
        return 0.0

    return total_distance / total_aksharas

"""Beam search decoding for CTC."""

import torch
import torch.nn.functional as F
from typing import List, Optional
import numpy as np


def beam_search_decode(
    logits: torch.Tensor,
    charset,
    beam_width: int = 10,
    blank_idx: int = 0,
) -> List[str]:
    """
    Beam search CTC decoding.

    Args:
        logits: Model outputs [B, T, num_classes]
        charset: Charset for decoding
        beam_width: Beam width
        blank_idx: Blank token index

    Returns:
        List of decoded strings
    """
    log_probs = F.log_softmax(logits, dim=-1)  # [B, T, num_classes]

    results = []

    for log_prob in log_probs:
        # Beam search for single sequence
        decoded = _beam_search_single(
            log_prob.cpu().numpy(),
            charset,
            beam_width=beam_width,
            blank_idx=blank_idx,
        )
        results.append(decoded)

    return results


def _beam_search_single(
    log_probs: np.ndarray,
    charset,
    beam_width: int = 10,
    blank_idx: int = 0,
) -> str:
    """
    Beam search for a single sequence.

    Simple prefix beam search implementation.

    Args:
        log_probs: Log probabilities [T, num_classes]
        charset: Charset
        beam_width: Beam width
        blank_idx: Blank index

    Returns:
        Decoded string
    """
    T, V = log_probs.shape

    # Initialize beams: (prefix, (p_blank, p_non_blank))
    beams = {(): (0.0, -np.inf)}  # Empty prefix

    for t in range(T):
        new_beams = {}

        for prefix, (p_b, p_nb) in beams.items():
            # Blank
            blank_prob = log_probs[t, blank_idx]
            new_p_b = np.logaddexp(p_b + blank_prob, p_nb + blank_prob)

            if prefix not in new_beams:
                new_beams[prefix] = (-np.inf, -np.inf)

            new_beams[prefix] = (
                np.logaddexp(new_beams[prefix][0], new_p_b),
                new_beams[prefix][1]
            )

            # Non-blank tokens
            for c in range(V):
                if c == blank_idx:
                    continue

                char_prob = log_probs[t, c]
                new_prefix = prefix + (c,)

                # Extend with new character
                if len(prefix) > 0 and prefix[-1] == c:
                    # Repeat character (requires blank)
                    new_p_nb = p_b + char_prob
                else:
                    # New character
                    new_p_nb = np.logaddexp(p_b + char_prob, p_nb + char_prob)

                if new_prefix not in new_beams:
                    new_beams[new_prefix] = (-np.inf, -np.inf)

                new_beams[new_prefix] = (
                    new_beams[new_prefix][0],
                    np.logaddexp(new_beams[new_prefix][1], new_p_nb)
                )

        # Prune beams
        # Sort by total probability
        sorted_beams = sorted(
            new_beams.items(),
            key=lambda x: np.logaddexp(x[1][0], x[1][1]),
            reverse=True
        )
        beams = dict(sorted_beams[:beam_width])

    # Get best beam
    best_prefix = max(
        beams.keys(),
        key=lambda x: np.logaddexp(beams[x][0], beams[x][1])
    )

    # Decode
    decoded = charset.decode(list(best_prefix), remove_duplicates=False)
    return decoded

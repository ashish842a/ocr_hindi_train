"""Evaluation engine."""

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from tqdm import tqdm
from typing import Dict, List

from ..decode import greedy_decode, beam_search_decode
from ..metrics import compute_cer, compute_wer


class Evaluator:
    """Evaluation engine for HTR models."""

    def __init__(
        self,
        model: nn.Module,
        charset,
        device: torch.device,
        decode_method: str = 'greedy',
        beam_width: int = 10,
    ):
        """
        Initialize evaluator.

        Args:
            model: HTR model
            charset: Charset for decoding
            device: Device
            decode_method: Decoding method ('greedy', 'beam')
            beam_width: Beam width for beam search
        """
        self.model = model
        self.charset = charset
        self.device = device
        self.decode_method = decode_method
        self.beam_width = beam_width

    @torch.no_grad()
    def evaluate(
        self,
        data_loader: DataLoader,
        return_predictions: bool = False,
    ) -> Dict:
        """
        Evaluate model on a dataset.

        Args:
            data_loader: Data loader
            return_predictions: Whether to return predictions

        Returns:
            Dictionary with metrics and optionally predictions
        """
        self.model.eval()

        all_predictions = []
        all_references = []

        pbar = tqdm(data_loader, desc='Evaluating')

        for batch in pbar:
            # Move to device
            images = batch['images'].to(self.device)
            input_lengths = batch['input_lengths'].to(self.device)
            texts = batch['texts']

            # Forward pass
            outputs = self.model(images, input_lengths=input_lengths)

            # Get logits (prefer CTC for decoding)
            if 'ctc_logits' in outputs:
                logits = outputs['ctc_logits']
            elif 'attention_logits' in outputs:
                logits = outputs['attention_logits']
            else:
                raise ValueError("No logits found in model outputs")

            # Decode
            if self.decode_method == 'greedy':
                predictions = greedy_decode(logits, self.charset)
            elif self.decode_method == 'beam':
                predictions = beam_search_decode(
                    logits,
                    self.charset,
                    beam_width=self.beam_width
                )
            else:
                raise ValueError(f"Unknown decode method: {self.decode_method}")

            all_predictions.extend(predictions)
            all_references.extend(texts)

        # Compute metrics
        cer = compute_cer(all_predictions, all_references)
        wer = compute_wer(all_predictions, all_references)

        results = {
            'cer': cer,
            'wer': wer,
            'num_samples': len(all_predictions),
        }

        if return_predictions:
            results['predictions'] = all_predictions
            results['references'] = all_references

        return results

    def predict(self, images: torch.Tensor, input_lengths: torch.Tensor = None) -> List[str]:
        """
        Predict on a batch of images.

        Args:
            images: Input images [B, C, H, W]
            input_lengths: Sequence lengths [B]

        Returns:
            List of predicted texts
        """
        self.model.eval()

        with torch.no_grad():
            images = images.to(self.device)
            if input_lengths is not None:
                input_lengths = input_lengths.to(self.device)

            outputs = self.model(images, input_lengths=input_lengths)

            if 'ctc_logits' in outputs:
                logits = outputs['ctc_logits']
            elif 'attention_logits' in outputs:
                logits = outputs['attention_logits']
            else:
                raise ValueError("No logits found")

            if self.decode_method == 'greedy':
                predictions = greedy_decode(logits, self.charset)
            else:
                predictions = beam_search_decode(
                    logits,
                    self.charset,
                    beam_width=self.beam_width
                )

        return predictions

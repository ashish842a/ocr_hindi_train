"""CTC loss wrapper."""

import torch
import torch.nn as nn


class CTCLoss(nn.Module):
    """CTC loss with proper handling of input/target lengths."""

    def __init__(self, blank_idx: int = 0, reduction: str = 'mean', zero_infinity: bool = True):
        """
        Initialize CTC loss.

        Args:
            blank_idx: Index of blank token
            reduction: Reduction method ('none', 'mean', 'sum')
            zero_infinity: Whether to zero infinite losses
        """
        super().__init__()

        self.ctc_loss = nn.CTCLoss(
            blank=blank_idx,
            reduction=reduction,
            zero_infinity=zero_infinity,
        )

    def forward(
        self,
        logits: torch.Tensor,
        targets: torch.Tensor,
        input_lengths: torch.Tensor,
        target_lengths: torch.Tensor,
    ) -> torch.Tensor:
        """
        Compute CTC loss.

        Args:
            logits: Model outputs [B, T, num_classes]
            targets: Target labels [B, S] (padded)
            input_lengths: Input sequence lengths [B]
            target_lengths: Target sequence lengths [B]

        Returns:
            CTC loss value
        """
        # CTC loss expects [T, B, num_classes]
        log_probs = torch.nn.functional.log_softmax(logits, dim=-1)
        log_probs = log_probs.permute(1, 0, 2)  # [T, B, num_classes]

        # Compute loss
        loss = self.ctc_loss(
            log_probs=log_probs,
            targets=targets,
            input_lengths=input_lengths,
            target_lengths=target_lengths,
        )

        return loss

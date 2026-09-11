"""Attention-based sequence loss."""

import torch
import torch.nn as nn
import torch.nn.functional as F


class AttentionLoss(nn.Module):
    """Cross-entropy loss for attention decoder."""

    def __init__(
        self,
        ignore_index: int = -100,
        label_smoothing: float = 0.0,
    ):
        """
        Initialize attention loss.

        Args:
            ignore_index: Index to ignore in loss computation
            label_smoothing: Label smoothing factor
        """
        super().__init__()

        self.criterion = nn.CrossEntropyLoss(
            ignore_index=ignore_index,
            label_smoothing=label_smoothing,
            reduction='mean',
        )

    def forward(
        self,
        logits: torch.Tensor,
        targets: torch.Tensor,
    ) -> torch.Tensor:
        """
        Compute attention loss.

        Args:
            logits: Model outputs [B, T, num_classes]
            targets: Target labels [B, T]

        Returns:
            Loss value
        """
        # Reshape for cross-entropy: [B*T, num_classes] and [B*T]
        B, T, C = logits.shape
        logits = logits.reshape(-1, C)
        targets = targets.reshape(-1)

        loss = self.criterion(logits, targets)
        return loss

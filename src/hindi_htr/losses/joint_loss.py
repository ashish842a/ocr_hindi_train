"""Joint CTC-Attention loss."""

import torch
import torch.nn as nn

from .ctc_loss import CTCLoss
from .attention_loss import AttentionLoss


class JointCTCAttentionLoss(nn.Module):
    """
    Joint CTC-Attention loss with weighting parameter λ.

    L = λ * L_ctc + (1 - λ) * L_att
    """

    def __init__(
        self,
        ctc_weight: float = 0.7,
        blank_idx: int = 0,
        ignore_index: int = -100,
        label_smoothing: float = 0.0,
    ):
        """
        Initialize joint loss.

        Args:
            ctc_weight: Weight for CTC loss (λ)
            blank_idx: Blank token index for CTC
            ignore_index: Ignore index for attention loss
            label_smoothing: Label smoothing for attention loss
        """
        super().__init__()

        self.ctc_weight = ctc_weight
        self.att_weight = 1.0 - ctc_weight

        self.ctc_loss = CTCLoss(blank_idx=blank_idx)
        self.att_loss = AttentionLoss(
            ignore_index=ignore_index,
            label_smoothing=label_smoothing,
        )

    def forward(
        self,
        ctc_logits: torch.Tensor,
        attention_logits: torch.Tensor,
        targets: torch.Tensor,
        input_lengths: torch.Tensor,
        target_lengths: torch.Tensor,
    ) -> dict:
        """
        Compute joint loss.

        Args:
            ctc_logits: CTC outputs [B, T_enc, num_classes]
            attention_logits: Attention outputs [B, T_dec, num_classes]
            targets: Target labels [B, T_dec]
            input_lengths: Encoder output lengths [B]
            target_lengths: Target sequence lengths [B]

        Returns:
            Dictionary with 'loss', 'ctc_loss', 'att_loss'
        """
        # CTC loss
        ctc_loss_value = self.ctc_loss(
            logits=ctc_logits,
            targets=targets,
            input_lengths=input_lengths,
            target_lengths=target_lengths,
        )

        # Attention loss
        att_loss_value = self.att_loss(
            logits=attention_logits,
            targets=targets,
        )

        # Weighted combination
        total_loss = self.ctc_weight * ctc_loss_value + self.att_weight * att_loss_value

        return {
            'loss': total_loss,
            'ctc_loss': ctc_loss_value.item(),
            'att_loss': att_loss_value.item(),
        }

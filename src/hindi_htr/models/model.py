"""Main HTR model assembly."""

import torch
import torch.nn as nn
from typing import Dict, Optional

from .backbones import ResNetBackbone, CRNNBackbone
from .necks import BiLSTMNeck, TransformerNeck
from .heads import CTCHead, AttentionHead, WriterAdversary


class HTRModel(nn.Module):
    """
    Handwritten Text Recognition model.

    Modular architecture: Backbone → Neck → Head(s)
    """

    def __init__(
        self,
        backbone_type: str = 'resnet50',
        neck_type: str = 'bilstm',
        head_type: str = 'ctc',
        num_classes: int = 100,
        num_writers: Optional[int] = None,
        backbone_config: Optional[Dict] = None,
        neck_config: Optional[Dict] = None,
        head_config: Optional[Dict] = None,
        use_writer_adversary: bool = False,
    ):
        """
        Initialize HTR model.

        Args:
            backbone_type: Type of backbone ('resnet50', 'crnn')
            neck_type: Type of neck ('bilstm', 'transformer', 'none')
            head_type: Type of head ('ctc', 'attention', 'joint')
            num_classes: Number of character classes
            num_writers: Number of writers (for adversary)
            backbone_config: Backbone configuration
            neck_config: Neck configuration
            head_config: Head configuration
            use_writer_adversary: Whether to use writer adversary
        """
        super().__init__()

        backbone_config = backbone_config or {}
        neck_config = neck_config or {}
        head_config = head_config or {}

        # Backbone
        if backbone_type == 'resnet50':
            self.backbone = ResNetBackbone(**backbone_config)
        elif backbone_type == 'crnn':
            self.backbone = CRNNBackbone(**backbone_config)
        else:
            raise ValueError(f"Unknown backbone: {backbone_type}")

        backbone_dim = self.backbone.out_channels

        # Neck
        if neck_type == 'bilstm':
            self.neck = BiLSTMNeck(
                input_dim=backbone_dim,
                **neck_config
            )
            neck_dim = self.neck.out_channels
        elif neck_type == 'transformer':
            self.neck = TransformerNeck(
                input_dim=backbone_dim,
                **neck_config
            )
            neck_dim = self.neck.out_channels
        elif neck_type == 'none':
            self.neck = nn.Identity()
            neck_dim = backbone_dim
        else:
            raise ValueError(f"Unknown neck: {neck_type}")

        # Head
        self.head_type = head_type

        if head_type == 'ctc':
            self.ctc_head = CTCHead(
                input_dim=neck_dim,
                num_classes=num_classes,
                **head_config
            )
            self.attention_head = None
        elif head_type == 'attention':
            self.ctc_head = None
            self.attention_head = AttentionHead(
                encoder_dim=neck_dim,
                num_classes=num_classes,
                **head_config
            )
        elif head_type == 'joint':
            # Joint CTC-Attention
            self.ctc_head = CTCHead(
                input_dim=neck_dim,
                num_classes=num_classes,
                **head_config.get('ctc_config', {})
            )
            self.attention_head = AttentionHead(
                encoder_dim=neck_dim,
                num_classes=num_classes,
                **head_config.get('attention_config', {})
            )
        else:
            raise ValueError(f"Unknown head: {head_type}")

        # Writer adversary
        if use_writer_adversary:
            if num_writers is None:
                raise ValueError("num_writers must be specified for writer adversary")
            self.writer_adversary = WriterAdversary(
                input_dim=neck_dim,
                num_writers=num_writers,
            )
        else:
            self.writer_adversary = None

    def forward(
        self,
        images: torch.Tensor,
        input_lengths: Optional[torch.Tensor] = None,
        targets: Optional[torch.Tensor] = None,
        writer_alpha: float = 1.0,
    ) -> Dict[str, torch.Tensor]:
        """
        Forward pass.

        Args:
            images: Input images [B, C, H, W]
            input_lengths: Sequence lengths [B]
            targets: Target labels [B, T] (for attention)
            writer_alpha: Gradient reversal strength for writer adversary

        Returns:
            Dictionary with model outputs
        """
        outputs = {}

        # Backbone
        features = self.backbone(images)  # [B, T, C]

        # input_lengths are already adjusted for backbone downsampling in collate_fn
        # Just clamp to actual feature size in case of any rounding differences
        if input_lengths is not None:
            adjusted_lengths = torch.clamp(input_lengths, max=features.size(1))
        else:
            adjusted_lengths = None

        # Neck
        if isinstance(self.neck, nn.Identity):
            encoded = features
        else:
            encoded = self.neck(features, lengths=adjusted_lengths)  # [B, T, C]

        # CTC head
        if self.ctc_head is not None:
            ctc_logits = self.ctc_head(encoded)  # [B, T, num_classes]
            outputs['ctc_logits'] = ctc_logits

        # Attention head
        if self.attention_head is not None:
            attention_logits = self.attention_head(
                encoder_outputs=encoded,
                targets=targets,
            )
            outputs['attention_logits'] = attention_logits

        # Writer adversary
        if self.writer_adversary is not None:
            writer_logits = self.writer_adversary(encoded, alpha=writer_alpha)
            outputs['writer_logits'] = writer_logits

        return outputs

    def freeze_backbone(self):
        """Freeze backbone parameters."""
        for param in self.backbone.parameters():
            param.requires_grad = False

    def unfreeze_backbone(self):
        """Unfreeze backbone parameters."""
        for param in self.backbone.parameters():
            param.requires_grad = True


def build_model(config: Dict) -> HTRModel:
    """
    Build model from configuration.

    Args:
        config: Model configuration dictionary

    Returns:
        HTRModel instance
    """
    return HTRModel(
        backbone_type=config.get('backbone_type', 'resnet50'),
        neck_type=config.get('neck_type', 'bilstm'),
        head_type=config.get('head_type', 'ctc'),
        num_classes=config['num_classes'],
        num_writers=config.get('num_writers'),
        backbone_config=config.get('backbone_config', {}),
        neck_config=config.get('neck_config', {}),
        head_config=config.get('head_config', {}),
        use_writer_adversary=config.get('use_writer_adversary', False),
    )

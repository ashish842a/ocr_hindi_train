"""Model architecture components."""

from .backbones import ResNetBackbone, CRNNBackbone
from .necks import BiLSTMNeck, TransformerNeck
from .heads import CTCHead, AttentionHead, WriterAdversary
from .model import HTRModel, build_model

__all__ = [
    "ResNetBackbone",
    "CRNNBackbone",
    "BiLSTMNeck",
    "TransformerNeck",
    "CTCHead",
    "AttentionHead",
    "WriterAdversary",
    "HTRModel",
    "build_model",
]

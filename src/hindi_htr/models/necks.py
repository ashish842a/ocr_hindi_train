"""Sequence modeling necks: BiLSTM and Transformer."""

import torch
import torch.nn as nn
from torch.nn.utils.rnn import pack_padded_sequence, pad_packed_sequence
import math


class BiLSTMNeck(nn.Module):
    """Bidirectional LSTM for sequence modeling."""

    def __init__(
        self,
        input_dim: int,
        hidden_dim: int = 512,
        num_layers: int = 2,
        dropout: float = 0.3,
    ):
        """
        Initialize BiLSTM neck.

        Args:
            input_dim: Input feature dimension
            hidden_dim: Hidden dimension per direction
            num_layers: Number of LSTM layers
            dropout: Dropout probability
        """
        super().__init__()

        self.lstm = nn.LSTM(
            input_size=input_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            dropout=dropout if num_layers > 1 else 0,
            bidirectional=True,
            batch_first=True,
        )

        self.out_channels = hidden_dim * 2  # Bidirectional

    def forward(
        self,
        x: torch.Tensor,
        lengths: torch.Tensor = None
    ) -> torch.Tensor:
        """
        Forward pass.

        Args:
            x: Input sequences [B, T, C]
            lengths: Sequence lengths [B] for packing (optional)

        Returns:
            Output sequences [B, T, hidden_dim*2]
        """
        if lengths is not None:
            # Pack for efficiency
            lengths_cpu = lengths.cpu()
            packed = pack_padded_sequence(
                x,
                lengths_cpu,
                batch_first=True,
                enforce_sorted=False,
            )
            output, _ = self.lstm(packed)
            output, _ = pad_packed_sequence(output, batch_first=True)
        else:
            output, _ = self.lstm(x)

        return output


class TransformerNeck(nn.Module):
    """Transformer encoder for sequence modeling."""

    def __init__(
        self,
        input_dim: int,
        hidden_dim: int = 512,
        num_layers: int = 4,
        num_heads: int = 8,
        dim_feedforward: int = 2048,
        dropout: float = 0.1,
    ):
        """
        Initialize Transformer neck.

        Args:
            input_dim: Input feature dimension
            hidden_dim: Model dimension
            num_layers: Number of transformer layers
            num_heads: Number of attention heads
            dim_feedforward: Feedforward dimension
            dropout: Dropout probability
        """
        super().__init__()

        # Project input to hidden_dim if needed
        if input_dim != hidden_dim:
            self.projection = nn.Linear(input_dim, hidden_dim)
        else:
            self.projection = nn.Identity()

        # Positional encoding
        self.pos_encoder = PositionalEncoding(hidden_dim, dropout)

        # Transformer encoder
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=hidden_dim,
            nhead=num_heads,
            dim_feedforward=dim_feedforward,
            dropout=dropout,
            batch_first=True,
        )

        self.transformer = nn.TransformerEncoder(
            encoder_layer,
            num_layers=num_layers,
        )

        self.out_channels = hidden_dim

    def forward(
        self,
        x: torch.Tensor,
        lengths: torch.Tensor = None
    ) -> torch.Tensor:
        """
        Forward pass.

        Args:
            x: Input sequences [B, T, C]
            lengths: Sequence lengths [B] for masking (optional)

        Returns:
            Output sequences [B, T, hidden_dim]
        """
        # Project
        x = self.projection(x)

        # Add positional encoding
        x = self.pos_encoder(x)

        # Create attention mask if lengths provided
        mask = None
        if lengths is not None:
            mask = self._create_mask(x.size(1), lengths, x.device)

        # Transformer
        output = self.transformer(x, src_key_padding_mask=mask)

        return output

    def _create_mask(
        self,
        seq_len: int,
        lengths: torch.Tensor,
        device: torch.device
    ) -> torch.Tensor:
        """
        Create padding mask.

        Args:
            seq_len: Maximum sequence length
            lengths: Actual lengths [B]
            device: Device

        Returns:
            Mask [B, seq_len] where True = padding position
        """
        batch_size = lengths.size(0)
        mask = torch.arange(seq_len, device=device)[None, :] >= lengths[:, None]
        return mask


class PositionalEncoding(nn.Module):
    """Sinusoidal positional encoding."""

    def __init__(self, d_model: int, dropout: float = 0.1, max_len: int = 5000):
        """
        Args:
            d_model: Model dimension
            dropout: Dropout probability
            max_len: Maximum sequence length
        """
        super().__init__()

        self.dropout = nn.Dropout(p=dropout)

        # Compute positional encodings
        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(
            torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model)
        )

        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)

        pe = pe.unsqueeze(0)  # [1, max_len, d_model]
        self.register_buffer('pe', pe)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Add positional encoding.

        Args:
            x: Input [B, T, C]

        Returns:
            Output with positional encoding [B, T, C]
        """
        x = x + self.pe[:, :x.size(1), :]
        return self.dropout(x)

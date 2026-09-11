"""Recognition heads: CTC, Attention, and Writer Adversary."""

import torch
import torch.nn as nn
import torch.nn.functional as F


class CTCHead(nn.Module):
    """CTC classification head."""

    def __init__(
        self,
        input_dim: int,
        num_classes: int,
        dropout: float = 0.3,
    ):
        """
        Initialize CTC head.

        Args:
            input_dim: Input feature dimension
            num_classes: Number of output classes (including blank)
            dropout: Dropout probability
        """
        super().__init__()

        self.dropout = nn.Dropout(dropout)
        self.classifier = nn.Linear(input_dim, num_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass.

        Args:
            x: Input sequences [B, T, C]

        Returns:
            Logits [B, T, num_classes]
        """
        x = self.dropout(x)
        logits = self.classifier(x)
        return logits


class AttentionHead(nn.Module):
    """
    Attention-based decoder head for sequence-to-sequence.

    Uses Bahdanau (additive) attention mechanism.
    """

    def __init__(
        self,
        encoder_dim: int,
        decoder_dim: int,
        num_classes: int,
        attention_dim: int = 256,
        dropout: float = 0.3,
    ):
        """
        Initialize attention decoder.

        Args:
            encoder_dim: Encoder output dimension
            decoder_dim: Decoder hidden dimension
            num_classes: Number of output classes
            attention_dim: Attention mechanism dimension
            dropout: Dropout probability
        """
        super().__init__()

        self.decoder_dim = decoder_dim
        self.num_classes = num_classes

        # Attention mechanism
        self.attention = BahdanauAttention(
            encoder_dim=encoder_dim,
            decoder_dim=decoder_dim,
            attention_dim=attention_dim,
        )

        # Decoder LSTM
        self.decoder_cell = nn.LSTMCell(
            input_size=num_classes + encoder_dim,  # prev output + context
            hidden_size=decoder_dim,
        )

        # Output projection
        self.dropout = nn.Dropout(dropout)
        self.fc = nn.Linear(decoder_dim + encoder_dim, num_classes)

    def forward(
        self,
        encoder_outputs: torch.Tensor,
        targets: torch.Tensor = None,
        max_length: int = None,
        teacher_forcing_ratio: float = 1.0,
    ) -> torch.Tensor:
        """
        Forward pass.

        Args:
            encoder_outputs: Encoder outputs [B, T_enc, C]
            targets: Target labels [B, T_dec] (for teacher forcing)
            max_length: Maximum decoding length (if targets not provided)
            teacher_forcing_ratio: Probability of using teacher forcing

        Returns:
            Output logits [B, T_dec, num_classes]
        """
        batch_size = encoder_outputs.size(0)
        device = encoder_outputs.device

        # Initialize decoder state
        h = torch.zeros(batch_size, self.decoder_dim, device=device)
        c = torch.zeros(batch_size, self.decoder_dim, device=device)

        # Start token (zeros)
        decoder_input = torch.zeros(batch_size, self.num_classes, device=device)

        # Determine decoding length
        if targets is not None:
            decode_length = targets.size(1)
        elif max_length is not None:
            decode_length = max_length
        else:
            decode_length = encoder_outputs.size(1)

        outputs = []

        for t in range(decode_length):
            # Attention
            context, _ = self.attention(encoder_outputs, h)

            # Decoder step
            lstm_input = torch.cat([decoder_input, context], dim=1)
            h, c = self.decoder_cell(lstm_input, (h, c))

            # Output projection
            output_input = torch.cat([h, context], dim=1)
            output = self.fc(self.dropout(output_input))

            outputs.append(output)

            # Teacher forcing
            if targets is not None and torch.rand(1).item() < teacher_forcing_ratio:
                # Use ground truth as next input
                decoder_input = F.one_hot(
                    targets[:, t],
                    num_classes=self.num_classes
                ).float()
            else:
                # Use prediction as next input
                decoder_input = F.softmax(output, dim=-1)

        outputs = torch.stack(outputs, dim=1)  # [B, T_dec, num_classes]
        return outputs


class BahdanauAttention(nn.Module):
    """Bahdanau (additive) attention mechanism."""

    def __init__(
        self,
        encoder_dim: int,
        decoder_dim: int,
        attention_dim: int = 256,
    ):
        """
        Args:
            encoder_dim: Encoder output dimension
            decoder_dim: Decoder hidden dimension
            attention_dim: Attention mechanism dimension
        """
        super().__init__()

        self.encoder_proj = nn.Linear(encoder_dim, attention_dim)
        self.decoder_proj = nn.Linear(decoder_dim, attention_dim)
        self.energy_proj = nn.Linear(attention_dim, 1)

    def forward(
        self,
        encoder_outputs: torch.Tensor,
        decoder_hidden: torch.Tensor,
    ) -> tuple:
        """
        Compute attention weights and context.

        Args:
            encoder_outputs: Encoder outputs [B, T, encoder_dim]
            decoder_hidden: Decoder hidden state [B, decoder_dim]

        Returns:
            Tuple of (context [B, encoder_dim], attention_weights [B, T])
        """
        # Project encoder outputs [B, T, attention_dim]
        encoder_proj = self.encoder_proj(encoder_outputs)

        # Project decoder hidden [B, 1, attention_dim]
        decoder_proj = self.decoder_proj(decoder_hidden).unsqueeze(1)

        # Compute energy [B, T, 1]
        energy = torch.tanh(encoder_proj + decoder_proj)
        energy = self.energy_proj(energy).squeeze(2)  # [B, T]

        # Attention weights
        attention_weights = F.softmax(energy, dim=1)  # [B, T]

        # Context vector [B, encoder_dim]
        context = torch.bmm(
            attention_weights.unsqueeze(1),  # [B, 1, T]
            encoder_outputs,  # [B, T, encoder_dim]
        ).squeeze(1)

        return context, attention_weights


class WriterAdversary(nn.Module):
    """
    Writer-adversarial branch for writer-invariant features.

    Uses gradient reversal to encourage encoder to produce writer-independent
    representations.
    """

    def __init__(
        self,
        input_dim: int,
        num_writers: int,
        hidden_dim: int = 256,
        dropout: float = 0.3,
    ):
        """
        Initialize writer adversary.

        Args:
            input_dim: Input feature dimension
            num_writers: Number of unique writers
            hidden_dim: Hidden layer dimension
            dropout: Dropout probability
        """
        super().__init__()

        self.classifier = nn.Sequential(
            nn.Dropout(dropout),
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(inplace=True),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, num_writers),
        )

    def forward(self, x: torch.Tensor, alpha: float = 1.0) -> torch.Tensor:
        """
        Forward pass with gradient reversal.

        Args:
            x: Input features [B, T, C] or [B, C]
            alpha: Gradient reversal strength

        Returns:
            Writer classification logits [B, num_writers]
        """
        # Apply gradient reversal
        x = GradientReversalLayer.apply(x, alpha)

        # Pool sequence if needed
        if x.dim() == 3:
            x = x.mean(dim=1)  # [B, C]

        # Classify
        logits = self.classifier(x)
        return logits


class GradientReversalLayer(torch.autograd.Function):
    """Gradient reversal layer for domain-adversarial training."""

    @staticmethod
    def forward(ctx, x, alpha):
        """Forward pass (identity)."""
        ctx.alpha = alpha
        return x.view_as(x)

    @staticmethod
    def backward(ctx, grad_output):
        """Backward pass (reverse gradient)."""
        return -ctx.alpha * grad_output, None

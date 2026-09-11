"""Encoder backbones for HTR.

Implements ResNet with stride correction and VGG-based CRNN baseline.
"""

import torch
import torch.nn as nn
from torchvision.models import resnet50, ResNet50_Weights
from typing import Tuple


class ResNetBackbone(nn.Module):
    """
    ResNet50 backbone with stride correction for sequence tasks.

    Standard ResNet50 has stride 32, which is too aggressive for CTC.
    We modify layer3 and layer4 to use (2,1) stride, resulting in:
    - Height stride: 32 (2^5)
    - Width stride: 4 (2^2)
    """

    def __init__(
        self,
        pretrained: bool = True,
        fix_stride: bool = True,
        frozen_stages: int = 0,
    ):
        """
        Initialize ResNet backbone.

        Args:
            pretrained: Whether to load ImageNet weights
            fix_stride: Whether to apply stride correction
            frozen_stages: Number of initial stages to freeze (0-4)
        """
        super().__init__()

        # Load pretrained ResNet50
        if pretrained:
            weights = ResNet50_Weights.IMAGENET1K_V1
            self.resnet = resnet50(weights=weights)
        else:
            self.resnet = resnet50(weights=None)

        # Remove FC layer and avgpool
        self.resnet.fc = nn.Identity()
        self.resnet.avgpool = nn.Identity()

        # Fix stride in layer3 and layer4
        if fix_stride:
            self._fix_stride()

        # Freeze early stages if requested
        if frozen_stages > 0:
            self._freeze_stages(frozen_stages)

        self.out_channels = 2048

    def _fix_stride(self):
        """
        Modify stride in layer3 and layer4 from (2,2) to (2,1).

        This keeps height collapsing while preserving width.
        """
        # Layer 3: modify first block's downsample
        self.resnet.layer3[0].conv2.stride = (2, 1)
        self.resnet.layer3[0].conv2.padding = (1, 1)
        if self.resnet.layer3[0].downsample is not None:
            self.resnet.layer3[0].downsample[0].stride = (2, 1)

        # Layer 4: modify first block's downsample
        self.resnet.layer4[0].conv2.stride = (2, 1)
        self.resnet.layer4[0].conv2.padding = (1, 1)
        if self.resnet.layer4[0].downsample is not None:
            self.resnet.layer4[0].downsample[0].stride = (2, 1)

    def _freeze_stages(self, num_stages: int):
        """Freeze early stages."""
        stages = [
            [self.resnet.conv1, self.resnet.bn1],
            [self.resnet.layer1],
            [self.resnet.layer2],
            [self.resnet.layer3],
            [self.resnet.layer4],
        ]

        for i in range(min(num_stages, len(stages))):
            for module in stages[i]:
                for param in module.parameters():
                    param.requires_grad = False

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Forward pass.

        Args:
            x: Input images [B, C, H, W]

        Returns:
            Tuple of:
            - Feature maps [B, C, H', W']
            - Sequence features [B, T, C] where T = W'
        """
        # Initial layers
        x = self.resnet.conv1(x)  # /2
        x = self.resnet.bn1(x)
        x = self.resnet.relu(x)
        x = self.resnet.maxpool(x)  # /2

        # ResNet stages
        x = self.resnet.layer1(x)  # /1
        x = self.resnet.layer2(x)  # /2
        x = self.resnet.layer3(x)  # /2 height, /1 width (if fixed)
        x = self.resnet.layer4(x)  # /2 height, /1 width (if fixed)

        # Output: [B, 2048, H', W']
        # Convert to sequence: [B, T, C]
        B, C, H, W = x.shape

        # Pool height dimension
        x = x.mean(dim=2)  # [B, C, W]
        x = x.permute(0, 2, 1)  # [B, W, C]

        return x


class CRNNBackbone(nn.Module):
    """
    VGG-style CNN backbone for CRNN baseline.

    Simpler architecture with conv-pool layers, stride /4 in width.
    """

    def __init__(
        self,
        input_channels: int = 1,
        hidden_dim: int = 256,
    ):
        """
        Initialize CRNN backbone.

        Args:
            input_channels: Number of input channels (1 for grayscale)
            hidden_dim: Hidden dimension
        """
        super().__init__()

        # VGG-style conv blocks
        self.features = nn.Sequential(
            # Conv 1
            nn.Conv2d(input_channels, 64, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2),  # /2

            # Conv 2
            nn.Conv2d(64, 128, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2),  # /4

            # Conv 3
            nn.Conv2d(128, 256, kernel_size=3, padding=1),
            nn.BatchNorm2d(256),
            nn.ReLU(inplace=True),

            # Conv 4
            nn.Conv2d(256, 256, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=(2, 1), stride=(2, 1)),  # /8 height, /4 width

            # Conv 5
            nn.Conv2d(256, 512, kernel_size=3, padding=1),
            nn.BatchNorm2d(512),
            nn.ReLU(inplace=True),

            # Conv 6
            nn.Conv2d(512, 512, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=(2, 1), stride=(2, 1)),  # /16 height, /4 width

            # Conv 7
            nn.Conv2d(512, hidden_dim, kernel_size=2, padding=0),
            nn.BatchNorm2d(hidden_dim),
            nn.ReLU(inplace=True),
        )

        self.out_channels = hidden_dim

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass.

        Args:
            x: Input images [B, C, H, W]

        Returns:
            Sequence features [B, T, C] where T = W/4
        """
        x = self.features(x)  # [B, C, H', W']

        # Pool height and convert to sequence
        B, C, H, W = x.shape
        x = x.mean(dim=2)  # [B, C, W]
        x = x.permute(0, 2, 1)  # [B, W, C]

        return x

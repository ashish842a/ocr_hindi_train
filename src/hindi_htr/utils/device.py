"""Device resolution and AMP context management.

Resolves to cuda → mps → cpu and gates AMP to CUDA only.
"""

import torch
from contextlib import nullcontext
from typing import Tuple


def get_device() -> torch.device:
    """
    Resolve device in priority order: CUDA → MPS → CPU.

    Returns:
        torch.device: The best available device
    """
    if torch.cuda.is_available():
        return torch.device("cuda")
    elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        return torch.device("mps")
    else:
        return torch.device("cpu")


def get_amp_context(device: torch.device, enabled: bool = True) -> Tuple[torch.autocast, bool]:
    """
    Get autocast context manager and scaler enable flag.

    AMP is only enabled on CUDA; other devices use nullcontext.

    Args:
        device: The device being used
        enabled: Whether AMP is requested in config

    Returns:
        Tuple of (autocast context manager, whether to use GradScaler)
    """
    use_amp = enabled and device.type == "cuda"

    if use_amp:
        return torch.autocast(device_type="cuda", dtype=torch.float16), True
    else:
        return nullcontext(), False

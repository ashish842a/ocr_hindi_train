"""PyTorch dataset for Hindi HTR."""

import torch
from torch.utils.data import Dataset
from pathlib import Path
from PIL import Image
from typing import List, Dict, Optional, Callable
import numpy as np

from .charset import Charset


class HindiHTRDataset(Dataset):
    """Dataset for Hindi handwritten text recognition."""

    def __init__(
        self,
        manifest: List[Dict],
        charset: Charset,
        data_root: str,
        transform: Optional[Callable] = None,
        target_height: int = 64,
        normalize: bool = True,
    ):
        """
        Initialize dataset.

        Args:
            manifest: List of manifest entries
            charset: Character set for encoding labels
            data_root: Root directory for images
            transform: Optional transform/augmentation function
            target_height: Target height for resizing (preserving aspect ratio)
            normalize: Whether to normalize images to [-1, 1]
        """
        self.manifest = manifest
        self.charset = charset
        self.data_root = Path(data_root)
        self.transform = transform
        self.target_height = target_height
        self.normalize = normalize

    def __len__(self) -> int:
        """Return dataset size."""
        return len(self.manifest)

    def __getitem__(self, idx: int) -> Dict:
        """
        Get a sample.

        Returns:
            Dictionary with 'image', 'label', 'text', 'length' keys
        """
        entry = self.manifest[idx]

        # Load image
        img_path = self.data_root / entry['image_path']
        image = Image.open(img_path).convert('RGB')  # Convert to RGB for ResNet

        # Resize preserving aspect ratio
        width, height = image.size
        scale = self.target_height / height
        new_width = int(width * scale)
        image = image.resize((new_width, self.target_height), Image.BILINEAR)

        # Convert to numpy for transforms
        image = np.array(image)

        # Apply transforms/augmentation
        if self.transform:
            image = self.transform(image)

        # Convert to tensor: [H, W, 3] -> [3, H, W]
        image = torch.from_numpy(image).permute(2, 0, 1).float()

        # Normalize to [-1, 1] or [0, 1]
        if self.normalize:
            image = (image / 127.5) - 1.0  # [-1, 1]
        else:
            image = image / 255.0  # [0, 1]

        # Encode label
        text = entry['text']
        label = self.charset.encode(text)

        return {
            'image': image,
            'label': torch.tensor(label, dtype=torch.long),
            'text': text,
            'length': len(label),
            'width': image.shape[2],
            'height': image.shape[1],
        }


class LMDBDataset(Dataset):
    """LMDB-backed dataset for faster loading (optional optimization)."""

    def __init__(
        self,
        lmdb_path: str,
        charset: Charset,
        transform: Optional[Callable] = None,
        target_height: int = 64,
        normalize: bool = True,
    ):
        """
        Initialize LMDB dataset.

        Args:
            lmdb_path: Path to LMDB database
            charset: Character set for encoding labels
            transform: Optional transform/augmentation function
            target_height: Target height for resizing
            normalize: Whether to normalize images
        """
        import lmdb

        self.env = lmdb.open(
            lmdb_path,
            max_readers=32,
            readonly=True,
            lock=False,
            readahead=False,
            meminit=False,
        )

        with self.env.begin(write=False) as txn:
            self.length = int(txn.get('num_samples'.encode()).decode())

        self.charset = charset
        self.transform = transform
        self.target_height = target_height
        self.normalize = normalize

    def __len__(self) -> int:
        """Return dataset size."""
        return self.length

    def __getitem__(self, idx: int) -> Dict:
        """Get a sample from LMDB."""
        import io
        from PIL import Image

        with self.env.begin(write=False) as txn:
            # Get image
            img_key = f'image_{idx:08d}'.encode()
            img_bytes = txn.get(img_key)
            image = Image.open(io.BytesIO(img_bytes)).convert('L')

            # Get text
            text_key = f'text_{idx:08d}'.encode()
            text = txn.get(text_key).decode('utf-8')

        # Resize
        width, height = image.size
        scale = self.target_height / height
        new_width = int(width * scale)
        image = image.resize((new_width, self.target_height), Image.BILINEAR)

        # Convert to numpy
        image = np.array(image)

        # Apply transforms
        if self.transform:
            image = self.transform(image)

        # Convert to tensor
        image = torch.from_numpy(image).unsqueeze(0).float()

        if self.normalize:
            image = (image / 127.5) - 1.0
        else:
            image = image / 255.0

        # Encode label
        label = self.charset.encode(text)

        return {
            'image': image,
            'label': torch.tensor(label, dtype=torch.long),
            'text': text,
            'length': len(label),
            'width': image.shape[2],
            'height': image.shape[1],
        }

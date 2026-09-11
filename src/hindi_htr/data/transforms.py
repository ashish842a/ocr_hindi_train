"""Image augmentation transforms for HTR.

Implements elastic distortion, affine, perspective, and morphological transforms.
"""

import numpy as np
import cv2
from typing import Optional, Tuple
import random


class Compose:
    """Compose multiple transforms."""

    def __init__(self, transforms):
        """
        Args:
            transforms: List of transform functions
        """
        self.transforms = transforms

    def __call__(self, image: np.ndarray) -> np.ndarray:
        """Apply transforms sequentially."""
        for t in self.transforms:
            image = t(image)
        return image


class RandomApply:
    """Apply transform with probability p."""

    def __init__(self, transform, p: float = 0.5):
        """
        Args:
            transform: Transform function
            p: Probability of applying
        """
        self.transform = transform
        self.p = p

    def __call__(self, image: np.ndarray) -> np.ndarray:
        """Apply transform with probability p."""
        if random.random() < self.p:
            return self.transform(image)
        return image


class ElasticDistortion:
    """Elastic distortion augmentation."""

    def __init__(
        self,
        alpha: float = 20.0,
        sigma: float = 3.0,
    ):
        """
        Args:
            alpha: Distortion magnitude
            sigma: Smoothness of distortion
        """
        self.alpha = alpha
        self.sigma = sigma

    def __call__(self, image: np.ndarray) -> np.ndarray:
        """Apply elastic distortion."""
        h, w = image.shape[:2]

        # Random displacement fields
        dx = np.random.randn(h, w).astype(np.float32)
        dy = np.random.randn(h, w).astype(np.float32)

        # Smooth with Gaussian
        dx = cv2.GaussianBlur(dx, None, self.sigma)
        dy = cv2.GaussianBlur(dy, None, self.sigma)

        # Scale
        dx *= self.alpha
        dy *= self.alpha

        # Create meshgrid
        x, y = np.meshgrid(np.arange(w), np.arange(h))
        map_x = (x + dx).astype(np.float32)
        map_y = (y + dy).astype(np.float32)

        # Remap
        distorted = cv2.remap(
            image,
            map_x,
            map_y,
            interpolation=cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_REFLECT,
        )

        return distorted


class RandomAffine:
    """Random affine transformation."""

    def __init__(
        self,
        rotation: float = 5.0,
        scale: Tuple[float, float] = (0.9, 1.1),
        shear: float = 5.0,
    ):
        """
        Args:
            rotation: Max rotation in degrees
            scale: Scale range (min, max)
            shear: Max shear in degrees
        """
        self.rotation = rotation
        self.scale = scale
        self.shear = shear

    def __call__(self, image: np.ndarray) -> np.ndarray:
        """Apply random affine transform."""
        h, w = image.shape[:2]
        center = (w / 2, h / 2)

        # Random parameters
        angle = random.uniform(-self.rotation, self.rotation)
        scale = random.uniform(*self.scale)
        shear_x = random.uniform(-self.shear, self.shear)

        # Rotation and scale matrix
        M = cv2.getRotationMatrix2D(center, angle, scale)

        # Add shear
        shear_rad = np.deg2rad(shear_x)
        M[0, 1] += np.tan(shear_rad) * M[0, 0]
        M[1, 1] += np.tan(shear_rad) * M[1, 0]

        # Apply
        transformed = cv2.warpAffine(
            image,
            M,
            (w, h),
            borderMode=cv2.BORDER_REFLECT,
        )

        return transformed


class RandomPerspective:
    """Random perspective transformation."""

    def __init__(self, distortion: float = 0.2):
        """
        Args:
            distortion: Distortion magnitude (0 to 1)
        """
        self.distortion = distortion

    def __call__(self, image: np.ndarray) -> np.ndarray:
        """Apply random perspective transform."""
        h, w = image.shape[:2]

        # Define source points (corners)
        src = np.array([
            [0, 0],
            [w - 1, 0],
            [w - 1, h - 1],
            [0, h - 1],
        ], dtype=np.float32)

        # Perturb destination points
        max_offset_w = w * self.distortion
        max_offset_h = h * self.distortion

        dst = src.copy()
        for i in range(4):
            dx = random.uniform(-max_offset_w, max_offset_w)
            dy = random.uniform(-max_offset_h, max_offset_h)
            dst[i] += [dx, dy]

        # Compute perspective matrix
        M = cv2.getPerspectiveTransform(src, dst)

        # Apply
        transformed = cv2.warpPerspective(
            image,
            M,
            (w, h),
            borderMode=cv2.BORDER_REFLECT,
        )

        return transformed


class RandomMorphology:
    """Random morphological operations (erosion/dilation)."""

    def __init__(self, kernel_size: int = 2):
        """
        Args:
            kernel_size: Size of morphological kernel
        """
        self.kernel_size = kernel_size

    def __call__(self, image: np.ndarray) -> np.ndarray:
        """Apply random erosion or dilation."""
        kernel = cv2.getStructuringElement(
            cv2.MORPH_ELLIPSE,
            (self.kernel_size, self.kernel_size)
        )

        op = random.choice(['erode', 'dilate', 'none'])

        if op == 'erode':
            return cv2.erode(image, kernel, iterations=1)
        elif op == 'dilate':
            return cv2.dilate(image, kernel, iterations=1)
        else:
            return image


class RandomGaussianNoise:
    """Add random Gaussian noise."""

    def __init__(self, sigma: float = 5.0):
        """
        Args:
            sigma: Standard deviation of noise
        """
        self.sigma = sigma

    def __call__(self, image: np.ndarray) -> np.ndarray:
        """Add Gaussian noise."""
        noise = np.random.randn(*image.shape) * self.sigma
        noisy = image + noise
        return np.clip(noisy, 0, 255).astype(image.dtype)


def get_train_transforms(config: dict) -> Compose:
    """
    Build training augmentation pipeline from config.

    Args:
        config: Augmentation configuration

    Returns:
        Composed transform
    """
    transforms = []

    if config.get('elastic', False):
        transforms.append(RandomApply(
            ElasticDistortion(
                alpha=config.get('elastic_alpha', 20.0),
                sigma=config.get('elastic_sigma', 3.0),
            ),
            p=config.get('elastic_p', 0.5),
        ))

    if config.get('affine', False):
        transforms.append(RandomApply(
            RandomAffine(
                rotation=config.get('affine_rotation', 5.0),
                scale=config.get('affine_scale', (0.9, 1.1)),
                shear=config.get('affine_shear', 5.0),
            ),
            p=config.get('affine_p', 0.5),
        ))

    if config.get('perspective', False):
        transforms.append(RandomApply(
            RandomPerspective(
                distortion=config.get('perspective_distortion', 0.2),
            ),
            p=config.get('perspective_p', 0.5),
        ))

    if config.get('morphology', False):
        transforms.append(RandomApply(
            RandomMorphology(
                kernel_size=config.get('morphology_kernel', 2),
            ),
            p=config.get('morphology_p', 0.3),
        ))

    if config.get('noise', False):
        transforms.append(RandomApply(
            RandomGaussianNoise(
                sigma=config.get('noise_sigma', 5.0),
            ),
            p=config.get('noise_p', 0.3),
        ))

    return Compose(transforms) if transforms else None

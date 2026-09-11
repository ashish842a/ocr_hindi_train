"""Bootstrap confidence intervals for metrics."""

import numpy as np
from typing import Callable, List, Tuple


def bootstrap_confidence_interval(
    predictions: List[str],
    references: List[str],
    metric_fn: Callable,
    n_resamples: int = 1000,
    confidence_level: float = 0.95,
    random_seed: int = 42,
) -> Tuple[float, float, float]:
    """
    Compute bootstrap confidence interval for a metric.

    Args:
        predictions: List of predictions
        references: List of references
        metric_fn: Metric function that takes (predictions, references)
        n_resamples: Number of bootstrap resamples
        confidence_level: Confidence level (e.g., 0.95 for 95%)
        random_seed: Random seed for reproducibility

    Returns:
        Tuple of (metric_value, lower_bound, upper_bound)
    """
    np.random.seed(random_seed)

    n_samples = len(predictions)
    metric_value = metric_fn(predictions, references)

    # Bootstrap resampling
    bootstrap_scores = []

    for _ in range(n_resamples):
        # Resample with replacement
        indices = np.random.choice(n_samples, size=n_samples, replace=True)
        resampled_preds = [predictions[i] for i in indices]
        resampled_refs = [references[i] for i in indices]

        # Compute metric
        score = metric_fn(resampled_preds, resampled_refs)
        bootstrap_scores.append(score)

    # Compute confidence interval
    alpha = 1 - confidence_level
    lower_percentile = (alpha / 2) * 100
    upper_percentile = (1 - alpha / 2) * 100

    lower_bound = np.percentile(bootstrap_scores, lower_percentile)
    upper_bound = np.percentile(bootstrap_scores, upper_percentile)

    return metric_value, lower_bound, upper_bound

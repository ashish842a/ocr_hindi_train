#!/usr/bin/env python3
"""
Training script for Hindi HTR.

Usage:
    python scripts/train.py --config configs/a1_baseline.yaml
"""

import argparse
import sys
from pathlib import Path
import torch
from torch.utils.data import DataLoader

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.hindi_htr.utils import (
    load_config, set_seed, get_device, setup_logger
)
from src.hindi_htr.data import (
    Charset, load_manifest, HindiHTRDataset,
    AspectRatioBucketSampler, collate_fn
)
from src.hindi_htr.data.transforms import get_train_transforms
from src.hindi_htr.models import build_model
from src.hindi_htr.losses import CTCLoss, JointCTCAttentionLoss
from src.hindi_htr.engine import Trainer


def main():
    parser = argparse.ArgumentParser(description='Train Hindi HTR model')
    parser.add_argument(
        '--config',
        type=str,
        required=True,
        help='Path to config YAML file'
    )
    parser.add_argument(
        '--resume',
        type=str,
        default=None,
        help='Path to checkpoint to resume from (or "auto" to auto-resume from latest)'
    )
    parser.add_argument(
        '--no-resume',
        action='store_true',
        help='Force fresh training, ignore existing checkpoints'
    )
    parser.add_argument(
        '--device',
        type=str,
        default=None,
        help='Device to use (overrides auto-detection)'
    )

    args = parser.parse_args()

    # Load config
    config = load_config(args.config)
    print(f"Loaded config from: {args.config}")

    # Set seed
    set_seed(config.get('seed', 42))

    # Get device
    if args.device:
        device = torch.device(args.device)
    else:
        device = get_device()

    print(f"Using device: {device}")

    # Setup logger
    log_dir = Path(config.get('log_dir', 'logs'))
    log_dir.mkdir(parents=True, exist_ok=True)

    from src.hindi_htr.utils.logging_utils import setup_logger
    logger = setup_logger(
        name='train',
        log_file=str(log_dir / 'train.log'),
    )

    logger.info("="*80)
    logger.info("Hindi HTR Training")
    logger.info("="*80)
    logger.info(f"Config: {args.config}")
    logger.info(f"Device: {device}")

    # Load charset
    charset_path = config['data']['charset_path']
    charset = Charset.load(charset_path)
    logger.info(f"Loaded charset: {len(charset)} classes")

    # Load manifests
    train_manifest = load_manifest(config['data']['train_manifest'])
    val_manifest = load_manifest(config['data']['val_manifest'])

    logger.info(f"Train samples: {len(train_manifest)}")
    logger.info(f"Val samples: {len(val_manifest)}")

    # Build datasets
    train_transforms = None
    if config.get('augmentation', {}).get('enabled', False):
        train_transforms = get_train_transforms(config['augmentation'])

    train_dataset = HindiHTRDataset(
        manifest=train_manifest,
        charset=charset,
        data_root=config['data']['data_root'],
        transform=train_transforms,
        target_height=config['data'].get('target_height', 64),
    )

    val_dataset = HindiHTRDataset(
        manifest=val_manifest,
        charset=charset,
        data_root=config['data']['data_root'],
        transform=None,  # No augmentation for validation
        target_height=config['data'].get('target_height', 64),
    )

    # Build data loaders
    if config['data'].get('use_bucket_sampler', True):
        train_sampler = AspectRatioBucketSampler(
            manifest=train_manifest,
            batch_size=config['training']['batch_size'],
            num_buckets=config['data'].get('num_buckets', 10),
            shuffle=True,
            drop_last=True,
        )
        train_loader = DataLoader(
            train_dataset,
            batch_sampler=train_sampler,
            collate_fn=collate_fn,
            num_workers=config['data'].get('num_workers', 4),
        )
    else:
        train_loader = DataLoader(
            train_dataset,
            batch_size=config['training']['batch_size'],
            shuffle=True,
            collate_fn=collate_fn,
            num_workers=config['data'].get('num_workers', 4),
        )

    val_loader = DataLoader(
        val_dataset,
        batch_size=config['training'].get('val_batch_size', config['training']['batch_size']),
        shuffle=False,
        collate_fn=collate_fn,
        num_workers=config['data'].get('num_workers', 4),
    )

    logger.info(f"Train batches: {len(train_loader)}")
    logger.info(f"Val batches: {len(val_loader)}")

    # Build model
    model_config = config['model']
    model_config['num_classes'] = len(charset)

    if model_config.get('use_writer_adversary', False):
        # Count unique writers in training data
        from collections import Counter
        writer_counts = Counter(e['writer_id'] for e in train_manifest)
        model_config['num_writers'] = len(writer_counts)
        logger.info(f"Writer adversary enabled: {model_config['num_writers']} writers")

    model = build_model(model_config)
    model = model.to(device)

    logger.info("Model built successfully")

    # Count parameters
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    logger.info(f"Total parameters: {total_params:,}")
    logger.info(f"Trainable parameters: {trainable_params:,}")

    # Build loss
    head_type = model_config.get('head_type', 'ctc')
    if head_type == 'joint':
        criterion = JointCTCAttentionLoss(
            ctc_weight=config['training'].get('ctc_weight', 0.7),
            blank_idx=charset.blank_idx,
        )
    else:
        criterion = CTCLoss(blank_idx=charset.blank_idx)

    logger.info(f"Loss function: {criterion.__class__.__name__}")

    # Build optimizer
    optimizer_config = config['training']['optimizer']
    if optimizer_config['type'] == 'adam':
        optimizer = torch.optim.Adam(
            model.parameters(),
            lr=optimizer_config['lr'],
            weight_decay=optimizer_config.get('weight_decay', 0),
        )
    elif optimizer_config['type'] == 'adamw':
        optimizer = torch.optim.AdamW(
            model.parameters(),
            lr=optimizer_config['lr'],
            weight_decay=optimizer_config.get('weight_decay', 1e-4),
        )
    else:
        raise ValueError(f"Unknown optimizer: {optimizer_config['type']}")

    logger.info(f"Optimizer: {optimizer.__class__.__name__}")
    logger.info(f"Learning rate: {optimizer_config['lr']}")

    # Build trainer
    trainer = Trainer(
        model=model,
        train_loader=train_loader,
        val_loader=val_loader,
        optimizer=optimizer,
        criterion=criterion,
        device=device,
        config=config['training'],
        logger=logger,
    )

    # Resume from checkpoint
    start_epoch = 1

    if not args.no_resume:
        # Check for auto-resume or explicit checkpoint
        if args.resume == 'auto' or args.resume is None:
            # Try to find latest checkpoint
            latest_checkpoint = trainer.find_latest_checkpoint()
            if latest_checkpoint:
                logger.info(f"Found existing checkpoint: {latest_checkpoint}")
                logger.info("Resuming from latest checkpoint (use --no-resume to start fresh)")
                start_epoch = trainer.load_checkpoint(latest_checkpoint)
            elif args.resume == 'auto':
                logger.info("No checkpoint found, starting fresh training")
        elif args.resume:
            # Explicit checkpoint path provided
            logger.info(f"Resuming from checkpoint: {args.resume}")
            start_epoch = trainer.load_checkpoint(args.resume)
    else:
        logger.info("--no-resume flag set, starting fresh training")

    # Train
    num_epochs = config['training']['num_epochs']
    logger.info(f"Starting training for {num_epochs} epochs (from epoch {start_epoch})")

    trainer.train(num_epochs=num_epochs, start_epoch=start_epoch)

    logger.info("Training complete!")


if __name__ == '__main__':
    main()

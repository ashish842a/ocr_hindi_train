"""Training engine."""

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from pathlib import Path
from tqdm import tqdm
import logging
import time
from typing import Optional, Dict

from ..losses import CTCLoss, JointCTCAttentionLoss
from ..utils.device import get_amp_context
from ..utils.metrics_logger import MetricsLogger


class Trainer:
    """Training engine for HTR models."""

    def __init__(
        self,
        model: nn.Module,
        train_loader: DataLoader,
        val_loader: Optional[DataLoader],
        optimizer: torch.optim.Optimizer,
        criterion: nn.Module,
        device: torch.device,
        config: Dict,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize trainer.

        Args:
            model: HTR model
            train_loader: Training data loader
            val_loader: Validation data loader
            optimizer: Optimizer
            criterion: Loss function
            device: Device
            config: Training configuration
            logger: Logger
        """
        self.model = model
        self.train_loader = train_loader
        self.val_loader = val_loader
        self.optimizer = optimizer
        self.criterion = criterion
        self.device = device
        self.config = config
        self.logger = logger or logging.getLogger(__name__)

        # AMP setup
        self.use_amp = config.get('use_amp', True)
        self.autocast, self.use_scaler = get_amp_context(device, self.use_amp)
        if self.use_scaler:
            self.scaler = torch.cuda.amp.GradScaler()
        else:
            self.scaler = None

        # Gradient clipping
        self.grad_clip = config.get('grad_clip', 5.0)

        # Learning rate scheduler
        self.scheduler = None
        if 'scheduler' in config:
            scheduler_config = config['scheduler']
            if scheduler_config['type'] == 'reduce_on_plateau':
                self.scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
                    optimizer,
                    mode=scheduler_config.get('mode', 'min'),
                    factor=scheduler_config.get('factor', 0.5),
                    patience=scheduler_config.get('patience', 5),
                    min_lr=scheduler_config.get('min_lr', 1e-6),
                    verbose=scheduler_config.get('verbose', True),
                )
                self.logger.info(f"LR Scheduler: ReduceLROnPlateau (patience={scheduler_config.get('patience', 5)})")
            elif scheduler_config['type'] == 'step':
                self.scheduler = torch.optim.lr_scheduler.StepLR(
                    optimizer,
                    step_size=scheduler_config.get('step_size', 10),
                    gamma=scheduler_config.get('gamma', 0.1),
                )
                self.logger.info(f"LR Scheduler: StepLR (step_size={scheduler_config.get('step_size', 10)})")
            elif scheduler_config['type'] == 'cosine':
                self.scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
                    optimizer,
                    T_max=scheduler_config.get('T_max', config.get('num_epochs', 50)),
                    eta_min=scheduler_config.get('min_lr', 1e-6),
                )
                self.logger.info(f"LR Scheduler: CosineAnnealingLR")

        # Checkpoint directory
        self.checkpoint_dir = Path(config.get('checkpoint_dir', 'checkpoints'))
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

        # Checkpoint saving frequency
        self.save_checkpoint_every = config.get('save_checkpoint_every', 5)

        # Metrics logger
        log_dir = Path(config.get('log_dir', 'logs'))
        experiment_name = config.get('experiment_name', 'experiment')
        self.metrics_logger = MetricsLogger(log_dir, experiment_name)
        self.logger.info(f"Metrics will be logged to: {log_dir}")

        # Best metrics
        self.best_val_loss = float('inf')
        self.best_epoch = 0

        # Training time tracking
        self.total_train_time = 0.0

    def train_epoch(self, epoch: int) -> Dict[str, float]:
        """
        Train for one epoch.

        Args:
            epoch: Current epoch number

        Returns:
            Dictionary of training metrics
        """
        self.model.train()

        total_loss = 0.0
        num_batches = 0

        pbar = tqdm(self.train_loader, desc=f'Epoch {epoch} [Train]')

        for batch in pbar:
            # Move to device
            images = batch['images'].to(self.device)
            labels = batch['labels'].to(self.device)
            input_lengths = batch['input_lengths'].to(self.device)
            label_lengths = batch['label_lengths'].to(self.device)

            # Forward pass with AMP
            with self.autocast:
                outputs = self.model(images, input_lengths=input_lengths)

                # Clamp input_lengths to actual sequence length
                # (input_lengths already accounts for backbone downsampling from collate_fn)
                ctc_input_lengths = torch.clamp(input_lengths, max=outputs['ctc_logits'].size(1))

                # Compute loss
                if isinstance(self.criterion, JointCTCAttentionLoss):
                    loss_dict = self.criterion(
                        ctc_logits=outputs['ctc_logits'],
                        attention_logits=outputs['attention_logits'],
                        targets=labels,
                        input_lengths=ctc_input_lengths,
                        target_lengths=label_lengths,
                    )
                    loss = loss_dict['loss']
                else:
                    loss = self.criterion(
                        logits=outputs['ctc_logits'],
                        targets=labels,
                        input_lengths=ctc_input_lengths,
                        target_lengths=label_lengths,
                    )

            # Backward pass
            self.optimizer.zero_grad()

            if self.scaler:
                self.scaler.scale(loss).backward()

                # Gradient clipping
                if self.grad_clip > 0:
                    self.scaler.unscale_(self.optimizer)
                    torch.nn.utils.clip_grad_norm_(
                        self.model.parameters(),
                        self.grad_clip
                    )

                self.scaler.step(self.optimizer)
                self.scaler.update()
            else:
                loss.backward()

                if self.grad_clip > 0:
                    torch.nn.utils.clip_grad_norm_(
                        self.model.parameters(),
                        self.grad_clip
                    )

                self.optimizer.step()

            # Update metrics
            total_loss += loss.item()
            num_batches += 1

            pbar.set_postfix({'loss': total_loss / num_batches})

        avg_loss = total_loss / num_batches

        return {'loss': avg_loss}

    @torch.no_grad()
    def validate(self, epoch: int) -> Dict[str, float]:
        """
        Validate model.

        Args:
            epoch: Current epoch number

        Returns:
            Dictionary of validation metrics
        """
        if self.val_loader is None:
            return {}

        self.model.eval()

        total_loss = 0.0
        num_batches = 0

        pbar = tqdm(self.val_loader, desc=f'Epoch {epoch} [Val]')

        for batch in pbar:
            # Move to device
            images = batch['images'].to(self.device)
            labels = batch['labels'].to(self.device)
            input_lengths = batch['input_lengths'].to(self.device)
            label_lengths = batch['label_lengths'].to(self.device)

            # Forward pass
            with self.autocast:
                outputs = self.model(images, input_lengths=input_lengths)

                # Clamp input_lengths to actual sequence length
                # (input_lengths already accounts for backbone downsampling from collate_fn)
                ctc_input_lengths = torch.clamp(input_lengths, max=outputs['ctc_logits'].size(1))

                # Compute loss
                if isinstance(self.criterion, JointCTCAttentionLoss):
                    loss_dict = self.criterion(
                        ctc_logits=outputs['ctc_logits'],
                        attention_logits=outputs['attention_logits'],
                        targets=labels,
                        input_lengths=ctc_input_lengths,
                        target_lengths=label_lengths,
                    )
                    loss = loss_dict['loss']
                else:
                    loss = self.criterion(
                        logits=outputs['ctc_logits'],
                        targets=labels,
                        input_lengths=ctc_input_lengths,
                        target_lengths=label_lengths,
                    )

            total_loss += loss.item()
            num_batches += 1

            pbar.set_postfix({'loss': total_loss / num_batches})

        avg_loss = total_loss / num_batches

        return {'loss': avg_loss}

    def save_checkpoint(self, epoch: int, metrics: Dict, is_best: bool = False):
        """
        Save model checkpoint.

        Args:
            epoch: Current epoch
            metrics: Metrics dictionary
            is_best: Whether this is the best model so far
        """
        checkpoint = {
            'epoch': epoch,
            'model_state_dict': self.model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'metrics': metrics,
            'config': self.config,
        }

        if self.scaler:
            checkpoint['scaler_state_dict'] = self.scaler.state_dict()

        if self.scheduler:
            checkpoint['scheduler_state_dict'] = self.scheduler.state_dict()

        # Always save latest checkpoint (for auto-resume)
        latest_path = self.checkpoint_dir / 'latest.pt'
        torch.save(checkpoint, latest_path)
        self.logger.info(f"Saved checkpoint: {latest_path}")

        # Save best checkpoint
        if is_best:
            best_path = self.checkpoint_dir / 'best.pt'
            torch.save(checkpoint, best_path)
            self.logger.info(f"Saved best checkpoint: {best_path}")

        # Save epoch checkpoint every N epochs
        if epoch % self.save_checkpoint_every == 0:
            epoch_path = self.checkpoint_dir / f'epoch_{epoch:03d}.pt'
            torch.save(checkpoint, epoch_path)
            self.logger.info(f"Saved epoch checkpoint: {epoch_path}")

    def load_checkpoint(self, checkpoint_path: str) -> int:
        """
        Load checkpoint.

        Args:
            checkpoint_path: Path to checkpoint

        Returns:
            Starting epoch
        """
        checkpoint = torch.load(checkpoint_path, map_location=self.device)

        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])

        if self.scaler and 'scaler_state_dict' in checkpoint:
            self.scaler.load_state_dict(checkpoint['scaler_state_dict'])

        if self.scheduler and 'scheduler_state_dict' in checkpoint:
            self.scheduler.load_state_dict(checkpoint['scheduler_state_dict'])

        epoch = checkpoint.get('epoch', 0)
        metrics = checkpoint.get('metrics', {})

        # Restore best metrics if available
        if 'val_loss' in metrics and metrics['val_loss'] < self.best_val_loss:
            self.best_val_loss = metrics['val_loss']
            self.best_epoch = epoch

        self.logger.info(f"Loaded checkpoint from epoch {epoch}")
        self.logger.info(f"Best val loss so far: {self.best_val_loss:.4f} at epoch {self.best_epoch}")

        return epoch + 1

    def find_latest_checkpoint(self) -> Optional[str]:
        """
        Find the latest checkpoint in checkpoint directory.

        Returns:
            Path to latest checkpoint or None
        """
        latest_path = self.checkpoint_dir / 'latest.pt'
        if latest_path.exists():
            return str(latest_path)
        return None

    def train(self, num_epochs: int, start_epoch: int = 1):
        """
        Full training loop.

        Args:
            num_epochs: Number of epochs to train
            start_epoch: Starting epoch (for resuming)
        """
        self.logger.info(f"Starting training for {num_epochs} epochs")

        for epoch in range(start_epoch, num_epochs + 1):
            epoch_start_time = time.time()

            # Train
            train_metrics = self.train_epoch(epoch)
            self.logger.info(f"Epoch {epoch} - Train Loss: {train_metrics['loss']:.4f}")

            # Validate
            val_metrics = self.validate(epoch)
            if val_metrics:
                self.logger.info(f"Epoch {epoch} - Val Loss: {val_metrics['loss']:.4f}")

                # Check if best
                is_best = val_metrics['loss'] < self.best_val_loss
                if is_best:
                    self.best_val_loss = val_metrics['loss']
                    self.best_epoch = epoch
                    self.logger.info(f"New best model at epoch {epoch}!")
            else:
                is_best = False

            # Calculate epoch time
            epoch_time = time.time() - epoch_start_time
            self.total_train_time += epoch_time

            # Get current learning rate
            current_lr = self.optimizer.param_groups[0]['lr']

            # Prepare metrics for logging
            log_metrics = {
                'train_loss': train_metrics['loss'],
                'learning_rate': current_lr,
                'epoch_time_seconds': epoch_time,
                'total_time_seconds': self.total_train_time,
                'total_time_hours': self.total_train_time / 3600,
            }

            # Add validation metrics if available
            if val_metrics:
                log_metrics['val_loss'] = val_metrics['loss']
                log_metrics['is_best'] = int(is_best)

            # Log metrics to CSV/JSON
            self.metrics_logger.log_epoch(epoch, log_metrics)

            # Update learning rate scheduler
            if self.scheduler is not None:
                if isinstance(self.scheduler, torch.optim.lr_scheduler.ReduceLROnPlateau):
                    # ReduceLROnPlateau needs the metric
                    if val_metrics:
                        self.scheduler.step(val_metrics['loss'])
                else:
                    # Other schedulers just need the epoch
                    self.scheduler.step()

            # Print timing info
            self.logger.info(
                f"Epoch {epoch} - Time: {epoch_time:.1f}s - "
                f"Total: {self.total_train_time/3600:.2f}h - LR: {current_lr:.6f}"
            )

            # Save checkpoint
            all_metrics = {**train_metrics, **{f'val_{k}': v for k, v in val_metrics.items()}}
            self.save_checkpoint(epoch, all_metrics, is_best=is_best)

        self.logger.info(f"Training complete! Best epoch: {self.best_epoch}")

        # Print final summary
        self.metrics_logger.print_summary()

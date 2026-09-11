#!/usr/bin/env python3
"""
Evaluation script for Hindi HTR.

Usage:
    python scripts/evaluate.py --config configs/a1_baseline.yaml --checkpoint checkpoints/best.pt
"""

import argparse
import sys
from pathlib import Path
import torch
import json
from torch.utils.data import DataLoader

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.hindi_htr.utils import load_config, get_device
from src.hindi_htr.data import (
    Charset, load_manifest, HindiHTRDataset, collate_fn
)
from src.hindi_htr.models import build_model
from src.hindi_htr.engine import Evaluator
from src.hindi_htr.metrics import bootstrap_confidence_interval, compute_cer, compute_wer


def main():
    parser = argparse.ArgumentParser(description='Evaluate Hindi HTR model')
    parser.add_argument(
        '--config',
        type=str,
        required=True,
        help='Path to config YAML file'
    )
    parser.add_argument(
        '--checkpoint',
        type=str,
        required=True,
        help='Path to model checkpoint'
    )
    parser.add_argument(
        '--split',
        type=str,
        default='test',
        choices=['train', 'val', 'test'],
        help='Dataset split to evaluate on'
    )
    parser.add_argument(
        '--decode-method',
        type=str,
        default='greedy',
        choices=['greedy', 'beam'],
        help='Decoding method'
    )
    parser.add_argument(
        '--beam-width',
        type=int,
        default=10,
        help='Beam width for beam search'
    )
    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='Output file for detailed results (JSON)'
    )
    parser.add_argument(
        '--bootstrap-ci',
        action='store_true',
        help='Compute bootstrap confidence intervals'
    )

    args = parser.parse_args()

    # Load config
    config = load_config(args.config)

    # Get device
    device = get_device()
    print(f"Using device: {device}")

    # Load charset
    charset_path = config['data']['charset_path']
    charset = Charset.load(charset_path)
    print(f"Loaded charset: {len(charset)} classes")

    # Load manifest
    if args.split == 'train':
        manifest_path = config['data']['train_manifest']
    elif args.split == 'val':
        manifest_path = config['data']['val_manifest']
    else:
        manifest_path = config['data']['test_manifest']

    manifest = load_manifest(manifest_path)
    print(f"Loaded {args.split} manifest: {len(manifest)} samples")

    # Build dataset
    dataset = HindiHTRDataset(
        manifest=manifest,
        charset=charset,
        data_root=config['data']['data_root'],
        transform=None,
        target_height=config['data'].get('target_height', 64),
    )

    data_loader = DataLoader(
        dataset,
        batch_size=config['training'].get('val_batch_size', 32),
        shuffle=False,
        collate_fn=collate_fn,
        num_workers=config['data'].get('num_workers', 4),
    )

    # Build model
    model_config = config['model']
    model_config['num_classes'] = len(charset)

    if model_config.get('use_writer_adversary', False):
        from collections import Counter
        writer_counts = Counter(e['writer_id'] for e in manifest)
        model_config['num_writers'] = len(writer_counts)

    model = build_model(model_config)
    model = model.to(device)

    # Load checkpoint
    print(f"Loading checkpoint: {args.checkpoint}")
    checkpoint = torch.load(args.checkpoint, map_location=device)
    model.load_state_dict(checkpoint['model_state_dict'])
    print(f"Checkpoint from epoch: {checkpoint.get('epoch', 'unknown')}")

    # Build evaluator
    evaluator = Evaluator(
        model=model,
        charset=charset,
        device=device,
        decode_method=args.decode_method,
        beam_width=args.beam_width,
    )

    # Evaluate
    print(f"\n{'='*80}")
    print(f"Evaluating on {args.split} set")
    print('=' * 80)

    results = evaluator.evaluate(data_loader, return_predictions=True)

    print(f"\nResults:")
    print(f"  CER: {results['cer']*100:.2f}%")
    print(f"  WER: {results['wer']*100:.2f}%")
    print(f"  Samples: {results['num_samples']}")

    # Bootstrap confidence intervals
    if args.bootstrap_ci:
        print(f"\nComputing bootstrap confidence intervals...")

        cer_val, cer_lower, cer_upper = bootstrap_confidence_interval(
            results['predictions'],
            results['references'],
            metric_fn=compute_cer,
            n_resamples=1000,
        )

        wer_val, wer_lower, wer_upper = bootstrap_confidence_interval(
            results['predictions'],
            results['references'],
            metric_fn=compute_wer,
            n_resamples=1000,
        )

        print(f"\nWith 95% confidence intervals:")
        print(f"  CER: {cer_val*100:.2f}% [{cer_lower*100:.2f}%, {cer_upper*100:.2f}%]")
        print(f"  WER: {wer_val*100:.2f}% [{wer_lower*100:.2f}%, {wer_upper*100:.2f}%]")

        results['cer_ci'] = [cer_lower, cer_upper]
        results['wer_ci'] = [wer_lower, wer_upper]

    # Per-writer breakdown (if writer_id available)
    if manifest and 'writer_id' in manifest[0]:
        print(f"\nPer-writer breakdown:")
        from collections import defaultdict

        writer_results = defaultdict(lambda: {'predictions': [], 'references': []})

        for i, entry in enumerate(manifest):
            writer_id = entry['writer_id']
            writer_results[writer_id]['predictions'].append(results['predictions'][i])
            writer_results[writer_id]['references'].append(results['references'][i])

        writer_metrics = {}
        for writer_id, data in sorted(writer_results.items()):
            cer = compute_cer(data['predictions'], data['references'])
            wer = compute_wer(data['predictions'], data['references'])
            num_samples = len(data['predictions'])

            writer_metrics[writer_id] = {
                'cer': cer,
                'wer': wer,
                'num_samples': num_samples,
            }

            print(f"  Writer {writer_id}: CER {cer*100:.2f}%, WER {wer*100:.2f}% ({num_samples} samples)")

        results['per_writer'] = writer_metrics
    else:
        results['per_writer'] = {}

    # Save detailed results
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Remove large fields for JSON export
        export_results = {
            'config': args.config,
            'checkpoint': args.checkpoint,
            'split': args.split,
            'decode_method': args.decode_method,
            'cer': results['cer'],
            'wer': results['wer'],
            'num_samples': results['num_samples'],
            'per_writer': results['per_writer'],
        }

        if args.bootstrap_ci:
            export_results['cer_ci'] = results['cer_ci']
            export_results['wer_ci'] = results['wer_ci']

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_results, f, ensure_ascii=False, indent=2)

        print(f"\nResults saved to: {output_path}")

        # Also save predictions separately
        predictions_path = output_path.with_suffix('.predictions.txt')
        with open(predictions_path, 'w', encoding='utf-8') as f:
            for pred, ref in zip(results['predictions'], results['references']):
                f.write(f"REF: {ref}\n")
                f.write(f"HYP: {pred}\n")
                f.write("\n")

        print(f"Predictions saved to: {predictions_path}")

    print(f"\n{'='*80}")
    print("Evaluation complete!")
    print('=' * 80)


if __name__ == '__main__':
    main()

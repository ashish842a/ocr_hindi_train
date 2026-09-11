#!/usr/bin/env python3
"""
Helper script to update MODEL_CHANGELOG.md with new experiment results.

Usage:
    python scripts/update_changelog.py --version v2 --cer 12.5 --wer 26.3
"""

import argparse
import json
from pathlib import Path
from datetime import datetime


def update_markdown_changelog(version, cer, wer, training_time=None):
    """Update MODEL_CHANGELOG.md with results."""

    changelog_path = Path('MODEL_CHANGELOG.md')

    if not changelog_path.exists():
        print(f"Error: {changelog_path} not found")
        return False

    content = changelog_path.read_text(encoding='utf-8')

    # Update the quick summary table
    version_line = f"| **{version}** |"

    # Find and replace TBD values for this version
    lines = content.split('\n')
    updated_lines = []

    for line in lines:
        if version_line in line and 'TBD' in line:
            # Replace TBD values
            line = line.replace('TBD', f'{cer:.2f}', 1)  # First TBD is CER
            line = line.replace('TBD', f'{wer:.2f}', 1)  # Second TBD is WER
            line = line.replace('🔄 Current', '✅ Complete')
            line = line.replace('📝 Planned', '✅ Complete')
        updated_lines.append(line)

    updated_content = '\n'.join(updated_lines)

    # Write back
    changelog_path.write_text(updated_content, encoding='utf-8')

    print(f"✅ Updated MODEL_CHANGELOG.md with {version} results:")
    print(f"   CER: {cer:.2f}%")
    print(f"   WER: {wer:.2f}%")

    return True


def main():
    parser = argparse.ArgumentParser(
        description='Update changelog with experiment results'
    )
    parser.add_argument('--version', type=str, required=True,
                        help='Version name (e.g., v2, v3)')
    parser.add_argument('--cer', type=float, required=True,
                        help='Character Error Rate (%)')
    parser.add_argument('--wer', type=float, required=True,
                        help='Word Error Rate (%)')
    parser.add_argument('--training-time', type=str,
                        help='Training time (e.g., "2.5h")')
    parser.add_argument('--results-json', type=str,
                        help='Path to results JSON file (auto-extract CER/WER)')

    args = parser.parse_args()

    # If results JSON provided, extract CER/WER
    if args.results_json:
        try:
            with open(args.results_json, 'r') as f:
                results = json.load(f)
                cer = results['cer'] * 100
                wer = results['wer'] * 100
                print(f"Loaded from {args.results_json}:")
                print(f"  CER: {cer:.2f}%")
                print(f"  WER: {wer:.2f}%")
        except Exception as e:
            print(f"Error reading results JSON: {e}")
            return
    else:
        cer = args.cer
        wer = args.wer

    # Update changelog
    success = update_markdown_changelog(
        args.version,
        cer,
        wer,
        args.training_time
    )

    if success:
        print("\n💡 Next steps:")
        print("1. Review MODEL_CHANGELOG.md")
        print("2. Update MODEL_CHANGELOG.html manually if needed")
        print("3. Commit the changes to git")


if __name__ == '__main__':
    main()

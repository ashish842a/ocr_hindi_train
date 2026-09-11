#!/bin/bash
# Quick evaluation script for V3 model

echo "=================================="
echo "Evaluating V3 Model on Test Set"
echo "=================================="

# Check if checkpoint exists
if [ ! -f "checkpoints/a1_baseline/best.pt" ]; then
    echo "❌ No checkpoint found at checkpoints/a1_baseline/best.pt"
    echo "Available checkpoints:"
    ls -lh checkpoints/a1_baseline/
    exit 1
fi

echo ""
echo "Running evaluation..."
echo ""

python scripts/evaluate.py \
    --config configs/a1_baseline.yaml \
    --checkpoint checkpoints/a1_baseline/best.pt \
    --split test \
    --bootstrap-ci \
    --output results/v3_test.json

echo ""
echo "=================================="
echo "Evaluation Complete!"
echo "=================================="
echo ""
echo "Results saved to: results/v3_test.json"
echo "Predictions saved to: results/v3_test.predictions.txt"


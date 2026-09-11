#!/bin/bash
# Wrapper script to run evaluation and save all terminal output to a log file

TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Default values
CONFIG_FILE=""
CHECKPOINT=""
SPLIT="test"
OUTPUT=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --config)
            CONFIG_FILE="$2"
            shift 2
            ;;
        --checkpoint)
            CHECKPOINT="$2"
            shift 2
            ;;
        --split)
            SPLIT="$2"
            shift 2
            ;;
        --output)
            OUTPUT="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

if [ -z "$CONFIG_FILE" ] || [ -z "$CHECKPOINT" ]; then
    echo "Error: Config and checkpoint required"
    echo "Usage: $0 --config <config> --checkpoint <checkpoint> [--split test] [--output results.json]"
    exit 1
fi

# Extract experiment name
EXPERIMENT_NAME=$(basename "$CONFIG_FILE" .yaml)

# Create logs directory
mkdir -p logs

# Log file path
LOG_FILE="logs/${EXPERIMENT_NAME}_eval_${SPLIT}_${TIMESTAMP}.log"

echo "Starting evaluation with:"
echo "  Config: $CONFIG_FILE"
echo "  Checkpoint: $CHECKPOINT"
echo "  Split: $SPLIT"
echo "Terminal output will be saved to: $LOG_FILE"
echo ""

# Build command
CMD="python scripts/evaluate.py --config $CONFIG_FILE --checkpoint $CHECKPOINT --split $SPLIT --bootstrap-ci"
if [ -n "$OUTPUT" ]; then
    CMD="$CMD --output $OUTPUT"
fi

# Run evaluation and capture all output
$CMD 2>&1 | tee "$LOG_FILE"

# Check exit status
EXIT_CODE=${PIPESTATUS[0]}

if [ $EXIT_CODE -eq 0 ]; then
    echo ""
    echo "Evaluation completed successfully!"
    echo "Full terminal log saved to: $LOG_FILE"
else
    echo ""
    echo "Evaluation failed with exit code: $EXIT_CODE"
    echo "Check log file for details: $LOG_FILE"
    exit $EXIT_CODE
fi

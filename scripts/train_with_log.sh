#!/bin/bash
# Wrapper script to run training and save all terminal output to a log file

if [ -z "$1" ]; then
    echo "Error: Config file required"
    echo "Usage: $0 <config_file>"
    echo "Example: $0 configs/a1_baseline.yaml"
    exit 1
fi

CONFIG_FILE=$1
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Extract experiment name from config file
EXPERIMENT_NAME=$(basename "$CONFIG_FILE" .yaml)

# Create logs directory
mkdir -p logs

# Log file path
LOG_FILE="logs/${EXPERIMENT_NAME}_terminal_${TIMESTAMP}.log"

echo "Starting training with config: $CONFIG_FILE"
echo "Terminal output will be saved to: $LOG_FILE"
echo ""

# Run training and capture all output (stdout and stderr) to both terminal and log file
python scripts/train.py --config "$CONFIG_FILE" 2>&1 | tee "$LOG_FILE"

# Check exit status
EXIT_CODE=${PIPESTATUS[0]}

if [ $EXIT_CODE -eq 0 ]; then
    echo ""
    echo "Training completed successfully!"
    echo "Full terminal log saved to: $LOG_FILE"
else
    echo ""
    echo "Training failed with exit code: $EXIT_CODE"
    echo "Check log file for details: $LOG_FILE"
    exit $EXIT_CODE
fi

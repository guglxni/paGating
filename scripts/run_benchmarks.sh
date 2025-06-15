#!/bin/bash

# Set cache directory to a local folder to avoid permission issues
export HF_HOME=$(pwd)/.cache
export TRANSFORMERS_CACHE=$(pwd)/.cache

# Activate conda environment
source $(conda info --base)/etc/profile.d/conda.sh
conda activate pagating_m4

# Ensure we are using the correct python
PYTHON_EXEC=$(which python)
echo "Using python: $PYTHON_EXEC"

# Run simple benchmark
echo -e "\n--- Running Simple Benchmark ---"
$PYTHON_EXEC scripts/simple_benchmark.py

# Run comprehensive benchmark
echo -e "\n--- Running Comprehensive Benchmark ---"
$PYTHON_EXEC scripts/benchmark_optimizations.py --alpha_mode learnable

# Run CoreML export test (replace with a real checkpoint when available)
# Note: This will fail until a model is trained and a checkpoint is saved.
# echo -e "\n--- Running CoreML Export Test ---"
# $PYTHON_EXEC scripts/export_to_coreml.py --model_path "path/to/your/checkpoint" --alpha_mode learnable --output_path "coreml_models/test.mlpackage" 
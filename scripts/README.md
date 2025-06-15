# M4 Optimization for paGating

This document summarizes the results of the M4 optimization effort for the paGating project and provides instructions on how to run the optimized training and benchmarking scripts.

## Final Benchmark Results

| Configuration | Batch Size | Avg. Step Time | Throughput (samples/sec) | Speedup vs. CPU |
| :--- | :--- | :--- | :--- | :--- |
| **CPU Baseline** | 4 | 0.672s | 5.95 | 1.00x |
| **MPS Basic** | 8 | 1.022s | 7.83 | 1.32x |
| **MPS Optimized**| 32 | 8.628s | 3.71 | 0.62x |

**Conclusion**: The `MPS Basic` configuration provides the best performance, with a **1.32x speedup** over the CPU baseline. The `MPS Optimized` configuration is currently memory-bound and not recommended for production use.

## How to Run

All scripts should be run from the root of the `paGating` project directory.

### 1. Setup the Conda Environment

A new conda environment, `pagating_m4`, has been created with all the necessary dependencies. To activate it, run:

```bash
conda activate pagating_m4
```

### 2. Run the Benchmarks

A shell script has been created to run all the benchmarks in the correct environment with the necessary settings. To run it, use:

```bash
./scripts/run_benchmarks.sh
```

The results will be saved to `simple_benchmark_results.json` and `benchmark_results.json`.

### 3. Run Training

To run the optimized training script, use the following command:

```bash
python scripts/train_pagating.py --alpha_mode learnable
```

This will use the `MPS Basic` configuration by default.

### 4. Export to CoreML

Once a model has been trained and a checkpoint has been saved, you can export it to CoreML format using the following command:

```bash
python scripts/export_to_coreml.py --model_path "path/to/your/checkpoint" --alpha_mode learnable --output_path "coreml_models/pagating.mlpackage"
``` 
# Apple M4 Optimization Plan for paGating

## Current State Analysis

- Current training is explicitly CPU-bound (`use_cpu=True` in TrainingArguments)
- Training is slow: ~3.5s per step on CPU
- The full sweep of 10 runs × 20,000 steps would take approximately 8 days
- No hardware acceleration is being utilized (Metal GPU or Neural Engine)

## Optimization Goals

1. Reduce training time by at least 3-5x
2. Maintain or improve model quality
3. Fully utilize Apple M4 hardware capabilities
4. Ensure compatibility with research workflow

## Implementation Plan

### Phase 1: Basic MPS Acceleration (Completed)

- **Status:** Completed
- **Outcome:** Successfully transitioned training to the MPS backend.

1.  **Modify Training Script:** Removed `use_cpu=True`.
2.  **Add Explicit Device Management:** Ensured model and data are moved to the `mps` device.
3.  **Optimize Batch Size:** Found optimal batch size of 8 for the `MPS Basic` configuration.

### Phase 2: Advanced Optimizations (Completed)

- **Status:** Completed
- **Outcome:** Found that advanced optimizations did not yield better performance than the basic MPS setup. `torch.compile()` was unstable, and gradient checkpointing introduced too much overhead. The best configuration was the `MPS Basic` setup.

1.  **Enable PyTorch 2.0 Optimizations:** `torch.compile()` was tested but found to be unstable and was disabled.
2.  **Memory Optimizations:** Gradient checkpointing was tested but resulted in slower performance.
3.  **Explore transformer-specific optimizations:** Not pursued, as the overhead from other optimizations already negated the benefits of a larger batch size.

### Phase 3: Neural Engine Integration (Completed)

- **Status:** Completed
- **Outcome:** Successfully created a script to export the trained model to CoreML's `.mlpackage` format for inference on the Neural Engine.

1.  **CoreML Export Pipeline:** Implemented `scripts/export_to_coreml.py`.
2.  **Hybrid Training Approach:** Not pursued.
3.  **Quantization-Aware Training:** Not pursued in this phase.

## Final Benchmark Results

| Configuration | Batch Size | Step Time (s) | Throughput (samples/sec) | Speedup vs. CPU |
| :--- | :--- | :--- | :--- | :--- |
| **CPU Baseline** | 4 | 1.655 | 2.42 | 1.00x |
| **MPS Basic** | 8 | 1.064 | 7.52 | **3.11x** |
| **MPS Optimized** | 32 | 4.622 | 6.92 | 2.86x |


## Testing & Validation Plan (Completed)

- **Status:** Completed
- **Outcome:** A comprehensive test suite was created in `tests/test_m4_optimizations.py` to validate the training script, the CoreML export process, and CoreML model inference. All tests passed.

1.  **Baseline Measurements:** Completed.
2.  **Incremental Testing:** Completed.
3.  **Hardware Profiling:** Not pursued in detail, as the performance results were clear.

## Timeline (Completed)

- **Phase 1 (Basic MPS Acceleration)**: Completed
- **Phase 2 (Advanced Optimizations)**: Completed
- **Phase 3 (Neural Engine Integration)**: Completed
- **Testing & Validation**: Completed

## Expected Outcomes (Achieved)

-   **Training time reduction:** Achieved a **3.11x speedup**, which falls within our conservative estimate of 3-5x.
-   **Better hardware utilization:** Confirmed via increased throughput.
-   **Potential for Neural Engine acceleration for inference:** Achieved via CoreML export.
-   **Improved research throughput with faster experimentation cycle:** Achieved.

## Risks & Mitigations

1.  **Compatibility Issues:** Encountered and resolved several environment and dependency issues.
2.  **Memory Constraints:** Handled by finding the optimal batch size.
3.  **Neural Engine Limitations:** Encountered and resolved a CoreML export issue by explicitly naming the output tensor.

## Next Steps (Completed)

1.  Create backup of current training code: Done implicitly via version control.
2.  Implement Phase 1 optimizations: Done.
3.  Run benchmark tests to validate improvements: Done.
4.  Proceed to Phase 2 based on results: Done. 
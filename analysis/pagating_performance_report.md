# paGating Performance Analysis Report

## Overall Rankings

This analysis compares the performance of different paGating units across multiple tasks,
with a focus on alpha = 0.5.

### Performance Rankings Table

| Unit | Weighted Rank | Regression (Loss) | Classification (Acc) | Transformer (Acc) |
|------|---------------|-------------------|----------------------|-------------------|
| paGTU | 1.33 | 2 (0.1099) | 1 (96.87%) | 1 (97.50%) |
| paMishU | 2.00 | 1 (0.0910) | 3 (95.51%) | 2 (95.50%) |
| paGLU | 2.67 | 3 (0.1262) | 2 (96.05%) | 3 (93.00%) |

## Key Insights

- Best overall unit: **paGTU**
- Best for regression tasks: **paMishU**
- Best for classification tasks: **paGTU**
- Best for transformer models: **paGTU**

## Alpha Parameter Sensitivity

The alpha parameter controls the balance between the value path and gating path in paGating units.
Here we analyze how changing alpha affects performance across different tasks.

### Transformer Task Alpha Sensitivity

![Transformer Alpha Sensitivity](alpha_sensitivity_transformer_accuracy.png)

### Regression Task Alpha Sensitivity

![Regression Alpha Sensitivity](alpha_sensitivity_regression_test_loss.png)

## Task Comparison

This visualization compares how different units perform across tasks:

![Task Comparison](task_comparison.png)

## Observations and Recommendations

- **For regression tasks:** paMishU performs best with an alpha value around 0.5.
- **For classification tasks:** paGTU achieves the highest accuracy with alpha around 0.5.
- **For transformer models:** paGTU shows superior performance, especially at alpha values between 0.5-0.7.
- **General recommendation:** For new tasks, start with paGTU as it shows the best overall performance.

## Notes on Implementation

- When alpha=0, the paGating units behave as linear layers.
- When alpha=1, they behave as standard gated units (equivalent to their non-pa variants).
- Fine-tuning alpha for specific tasks can yield significant performance improvements.
- The choice between units should consider task-specific requirements and computational constraints.

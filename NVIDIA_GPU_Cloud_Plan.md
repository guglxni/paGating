# Definitive NVIDIA GPU Cloud Computing Plan for paGating

## Overview

This document outlines a concrete, streamlined plan for running the paGating framework on NVIDIA GPUs using Vast.ai, focusing on a hassle-free approach with clear implementation steps.

## Why Vast.ai for paGating

After evaluating multiple cloud platforms, Vast.ai emerges as the optimal solution for our specific needs:

- **Superior Performance**: RTX 4090 GPUs provide approximately 10-15x speedup compared to the Mac Mini M4
- **Cost-Effective**: $0.35/hour for RTX 4090 (~$7/day) - significantly cheaper than AWS/GCP alternatives
- **Simplified Workflow**: Direct Docker container deployment with minimal setup complexity
- **Flexibility**: On-demand instances with pay-as-you-go pricing model
- **No Complex Account Approvals**: Quick signup without educational verification processes

## Current Performance Baseline

Based on our current runs on the Mac Mini M4:
- Average processing speed: ~3.04 seconds per step
- Full 20,000 steps sweep with 10 configurations: ~168 hours (7+ days)
- Memory constraints limiting batch size to 4

## Implementation Plan

### Step 1: Vast.ai Account Setup (15 minutes)

1. Create account at vast.ai
2. Add payment method (credit card)
3. Set spending limit alert at $50 for safety

### Step 2: Create Docker Container (30 minutes)

```dockerfile
FROM nvidia/cuda:12.0.0-runtime-ubuntu22.04

# System dependencies
RUN apt-get update && apt-get install -y python3-pip git

# Install PyTorch with CUDA
RUN pip3 install torch==2.0.1 torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Install dependencies
RUN pip3 install transformers==4.30.2 datasets tensorboard

# Clone your repository (use your actual repo)
WORKDIR /workspace
RUN git clone https://github.com/yourusername/paGating.git
WORKDIR /workspace/paGating

# Custom requirements
RUN pip3 install -r requirements.txt
```

### Step 3: Data Transfer Strategy (1 hour)

1. Create a compressed archive of your dataset
   ```bash
   # On your local machine
   tar -czvf dataset.tar.gz /path/to/your/dataset
   ```

2. Upload to cloud storage (Google Drive or Dropbox)

3. Add download script to your repository
   ```python
   # download_data.py
   import os
   import gdown
   
   # Download from Google Drive
   url = 'your-gdrive-file-id'
   output = 'dataset.tar.gz'
   gdown.download(id=url, output=output, quiet=False)
   
   # Extract
   os.system('tar -xzvf dataset.tar.gz')
   print("Dataset downloaded and extracted")
   ```

### Step 4: GPU Instance Setup (5 minutes)

1. Go to https://cloud.vast.ai/
2. Filter for:
   - GPU: RTX 4090
   - Reliability: 95%+
   - Disk Space: 50GB+
   - Internet: 100Mbps+
   
3. Select an instance (~$0.35/hour)
4. Configure:
   - On-demand (not interruptible)
   - Docker image: Your custom image or `pytorch/pytorch:2.0.1-cuda11.8-cudnn8-runtime`
   - Startup script:
     ```bash
     git clone https://github.com/yourusername/paGating.git
     cd paGating
     python download_data.py
     python scripts/train_pagating.py --alpha_mode static_0.0 --learning_rate 5e-4 --batch_size 16 --max_steps 20000 --output_dir logs/phase2_sweeps
     ```

### Step 5: Experiment Execution Strategy (3-5 days total)

1. Start with a single run to validate the setup
2. Expected performance: ~0.2-0.3s per step (vs. current ~3.04s)
3. Implement checkpoint saving for safety:
   ```python
   # Add to your training script
   if step % 1000 == 0:
       model.save_pretrained(f"{output_dir}/checkpoint-{step}")
       # Upload to cloud storage if needed
   ```

4. Once validated, create a sweep script to run all 10 experiments sequentially:
   ```python
   # run_all_experiments.py
   import subprocess
   import time
   
   alphas = ["static_0.0", "static_0.5", "static_1.0", "learnable", "scheduler_cosine"]
   learning_rates = [5e-4, 1e-3]
   
   for alpha in alphas:
       for lr in learning_rates:
           cmd = f"python scripts/train_pagating.py --alpha_mode {alpha} --learning_rate {lr} --batch_size 16 --max_steps 20000 --output_dir logs/phase2_sweeps/{alpha}_lr{lr}"
           print(f"Running: {cmd}")
           subprocess.run(cmd, shell=True)
           # Allow time for logs to flush
           time.sleep(10)
   ```

### Step 6: Cost Management and Output Handling

- RTX 4090 @ $0.35/hour
- Each experiment (~20,000 steps) should take ~2-3 hours (vs. ~15 hours on Mac)
- All 10 experiments: ~25-30 hours total = ~$10-12 total cost
- Upload checkpoints to persistent storage periodically
- Download results after each experiment completes

## Complete Timeline

- **Day 1**: Setup Vast.ai account, create Docker container, prepare data transfer
- **Day 2**: Run first experiment, validate performance, adjust as needed
- **Days 3-5**: Run remaining experiments in batches
- **Day 6**: Download and analyze all results

## Expected Performance Improvement

| Metric | Mac Mini M4 | Vast.ai (RTX 4090) | Improvement |
|--------|------------|-----------------|-------------|
| Time per step | ~3.04s | ~0.25s | 12x faster |
| Single experiment (20K steps) | ~16.9 hours | ~1.4 hours | 12x faster |
| Complete sweep (10 runs) | ~7 days | ~14 hours | 12x faster |
| Batch size | 4 | 16 | 4x larger |
| Total cost | Electricity + time | ~$12 | Time-efficient |

## Next Steps

1. Sign up for Vast.ai account
2. Prepare Docker container and data transfer scripts
3. Run initial test experiment
4. Execute full sweep
5. Download and analyze results 
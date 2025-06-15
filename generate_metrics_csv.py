#!/usr/bin/env python
"""
Generate metrics CSV files for the CIFAR-10 dashboard.

This script extracts metrics from training logs and generates CSV files
for each paGating unit to be used by the dashboard.
"""

import os
import json
import pandas as pd
import glob
import re
from typing import Dict, List, Optional, Union, Any

# Define paths
LOGS_DIR = "logs/cifar10"
LIGHTNING_DIR = "lightning_outputs"

def ensure_directories():
    """Ensure necessary directories exist."""
    os.makedirs(LOGS_DIR, exist_ok=True)
    for unit in ["paGLU", "paGTU", "paSwishU", "paReGLU", "paGELU", "paMishU", "paSiLU"]:
        os.makedirs(os.path.join(LOGS_DIR, unit), exist_ok=True)

def extract_metrics_from_lightning(unit_name: str) -> Optional[pd.DataFrame]:
    """
    Extract metrics from PyTorch Lightning logs for a specific unit.
    
    Args:
        unit_name: Name of the paGating unit
        
    Returns:
        DataFrame with extracted metrics or None if no logs found
    """
    # Find log directories for this unit
    pattern = f"{unit_name}_alpha*"
    log_dirs = glob.glob(os.path.join(LIGHTNING_DIR, pattern))
    
    if not log_dirs:
        print(f"No Lightning logs found for {unit_name}")
        return None
    
    # Use the most recent log directory
    log_dir = max(log_dirs, key=os.path.getmtime)
    
    # Look for metrics.csv or events file
    metrics_file = os.path.join(log_dir, "metrics.csv")
    if os.path.exists(metrics_file):
        df = pd.read_csv(metrics_file)
        # Process dataframe to extract relevant metrics
        metrics_df = process_lightning_metrics(df)
        return metrics_df
    
    # If no metrics.csv, look for TensorBoard event files
    events_files = glob.glob(os.path.join(log_dir, "events.out.tfevents.*"))
    if events_files:
        print(f"Found TensorBoard events for {unit_name}, but cannot extract metrics directly.")
        print(f"Please use TensorBoard to export metrics as CSV first.")
        return None
    
    return None

def process_lightning_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Process Lightning metrics dataframe into the required format.
    
    Args:
        df: Raw metrics dataframe from Lightning
        
    Returns:
        Processed dataframe with required columns
    """
    # Extract relevant columns and rename them
    metrics_df = pd.DataFrame()
    
    # Map Lightning column names to our format
    column_mapping = {
        "epoch": "epoch",
        "train_loss": "train_loss",
        "train_acc": "train_acc",
        "val_loss": "val_loss", 
        "val_acc": "val_acc",
        "alpha": "alpha"  # For learnable alpha
    }
    
    # Some Lightning logs use different column names
    alternate_mappings = {
        "train/loss": "train_loss",
        "train/acc": "train_acc",
        "val/loss": "val_loss",
        "val/acc": "val_acc",
        "alpha/value": "alpha"
    }
    
    # First try direct mapping
    for target, source in column_mapping.items():
        if source in df.columns:
            metrics_df[target] = df[source]
        else:
            # Try alternate mappings
            for alt_source, alt_target in alternate_mappings.items():
                if alt_source in df.columns and alt_target == source:
                    metrics_df[target] = df[alt_source]
                    break
    
    # Check if we got the required columns
    required = ["epoch", "train_loss", "train_acc", "val_loss", "val_acc"]
    if not all(col in metrics_df.columns for col in required):
        print(f"Warning: Could not find all required columns: {required}")
        print(f"Available columns: {df.columns.tolist()}")
        return pd.DataFrame()  # Empty dataframe
    
    return metrics_df

def extract_metrics_from_json(unit_name: str) -> Optional[pd.DataFrame]:
    """
    Extract metrics from JSON log files for a specific unit.
    
    Args:
        unit_name: Name of the paGating unit
        
    Returns:
        DataFrame with extracted metrics or None if no logs found
    """
    # Check for JSON files in unit comparison directory
    comparison_dir = "unit_comparison"
    if os.path.exists(comparison_dir):
        json_files = glob.glob(os.path.join(comparison_dir, "results_*.json"))
        if json_files:
            # Use the most recent file
            json_file = max(json_files, key=os.path.getmtime)
            with open(json_file, 'r') as f:
                results = json.load(f)
            
            if unit_name in results:
                # Extract metrics
                unit_results = results[unit_name]
                # These results typically only have final metrics
                # We'll create a simple DataFrame with just one row
                df = pd.DataFrame({
                    "epoch": [1],
                    "train_acc": [unit_results.get("train_acc", 0.0)],
                    "val_acc": [unit_results.get("val_acc", 0.0)],
                    "train_loss": [unit_results.get("train_loss", 0.0)],
                    "val_loss": [unit_results.get("val_loss", 0.0)]
                })
                return df
    
    return None

def extract_metrics_from_log_files(unit_name: str) -> Optional[pd.DataFrame]:
    """
    Extract metrics from log files for a specific unit.
    
    Args:
        unit_name: Name of the paGating unit
        
    Returns:
        DataFrame with extracted metrics or None if no logs found
    """
    # Look for log files
    log_files = glob.glob(f"{unit_name}*.log") + glob.glob(f"*{unit_name}*.log")
    
    if not log_files:
        print(f"No log files found for {unit_name}")
        return None
    
    # Use the most recent log file
    log_file = max(log_files, key=os.path.getmtime)
    
    # Extract metrics using regex
    epoch_pattern = r"Epoch\s+(\d+)"
    train_loss_pattern = r"train_loss[:\s]+([0-9.]+)"
    val_loss_pattern = r"val_loss[:\s]+([0-9.]+)"
    train_acc_pattern = r"train_acc[:\s]+([0-9.]+)"
    val_acc_pattern = r"val_acc[:\s]+([0-9.]+)"
    alpha_pattern = r"alpha[:\s]+([0-9.]+)"
    
    epochs = []
    train_losses = []
    val_losses = []
    train_accs = []
    val_accs = []
    alphas = []
    
    with open(log_file, 'r') as f:
        content = f.read()
        
        # Find all occurrences of metrics
        epoch_matches = re.findall(epoch_pattern, content)
        train_loss_matches = re.findall(train_loss_pattern, content)
        val_loss_matches = re.findall(val_loss_pattern, content)
        train_acc_matches = re.findall(train_acc_pattern, content)
        val_acc_matches = re.findall(val_acc_pattern, content)
        alpha_matches = re.findall(alpha_pattern, content)
        
        # Convert to appropriate types
        epochs = [int(e) for e in epoch_matches]
        train_losses = [float(l) for l in train_loss_matches]
        val_losses = [float(l) for l in val_loss_matches]
        train_accs = [float(a) for a in train_acc_matches]
        val_accs = [float(a) for a in val_acc_matches]
        alphas = [float(a) for a in alpha_matches]
    
    # Create DataFrame
    if epochs:
        # Make sure all lists have the same length
        min_len = min(len(epochs), len(train_losses), len(val_losses), 
                    len(train_accs), len(val_accs))
        
        data = {
            "epoch": epochs[:min_len],
            "train_loss": train_losses[:min_len],
            "val_loss": val_losses[:min_len],
            "train_acc": train_accs[:min_len],
            "val_acc": val_accs[:min_len]
        }
        
        if alphas:
            data["alpha"] = alphas[:min(min_len, len(alphas))]
        
        return pd.DataFrame(data)
    
    return None

def generate_metrics_csv():
    """Generate metrics CSV files for all units."""
    ensure_directories()
    
    units = ["paGLU", "paGTU", "paSwishU", "paReGLU", "paGELU", "paMishU", "paSiLU"]
    
    for unit in units:
        # Try different sources for metrics
        df = extract_metrics_from_lightning(unit)
        
        if df is None or df.empty:
            df = extract_metrics_from_json(unit)
        
        if df is None or df.empty:
            df = extract_metrics_from_log_files(unit)
        
        if df is not None and not df.empty:
            # Save to CSV
            output_path = os.path.join(LOGS_DIR, unit, "metrics.csv")
            df.to_csv(output_path, index=False)
            print(f"Generated metrics for {unit} at {output_path}")
        else:
            print(f"Could not find metrics for {unit}, skipping.")

if __name__ == "__main__":
    generate_metrics_csv() 
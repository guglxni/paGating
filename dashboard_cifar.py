#!/usr/bin/env python
"""
CIFAR-10 Performance Dashboard for paGating Units

This Streamlit app visualizes and compares the performance of 
different paGating units trained on the CIFAR-10 dataset.
"""

import os
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import glob
import json
from datetime import datetime
from typing import List, Dict, Optional, Union, Tuple

# Set page config
st.set_page_config(
    page_title="paGating CIFAR-10 Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Define paths
LOGS_DIR = "logs/cifar10"
UNITS = ["paGLU", "paGTU", "paReGLU", "paGELU", "paSiLU", "paMishU", "paSwishU"]
COLOR_MAP = {
    "paGLU": "#1f77b4",
    "paGTU": "#ff7f0e",
    "paReGLU": "#2ca02c",
    "paGELU": "#d62728",
    "paSiLU": "#9467bd",
    "paMishU": "#8c564b",
    "paSwishU": "#e377c2",
}

# Helper functions
def load_metrics(unit_name: str) -> Optional[pd.DataFrame]:
    """Load metrics from CSV file for a specific unit."""
    metrics_path = os.path.join(LOGS_DIR, unit_name, "metrics.csv")
    if not os.path.exists(metrics_path):
        return None
    
    try:
        df = pd.read_csv(metrics_path)
        # Ensure columns are properly named
        if 'epoch' not in df.columns:
            # Try to infer epoch column
            for col in df.columns:
                if 'epoch' in col.lower():
                    df.rename(columns={col: 'epoch'}, inplace=True)
                    break
            else:
                # If no epoch column found, create one
                df['epoch'] = range(1, len(df) + 1)
        
        # Ensure other columns exist or set them to NaN
        required_cols = ['train_loss', 'val_loss', 'train_acc', 'val_acc']
        for col in required_cols:
            if col not in df.columns:
                # Try to find matching column
                for existing_col in df.columns:
                    if col.lower() in existing_col.lower():
                        df.rename(columns={existing_col: col}, inplace=True)
                        break
                else:
                    df[col] = np.nan
        
        # Check if alpha exists
        has_alpha = any(col for col in df.columns if 'alpha' in col.lower())
        if has_alpha and 'alpha' not in df.columns:
            # Find alpha column and rename it
            for col in df.columns:
                if 'alpha' in col.lower():
                    df.rename(columns={col: 'alpha'}, inplace=True)
                    break
        
        return df
    except Exception as e:
        st.error(f"Error loading metrics for {unit_name}: {e}")
        return None

def get_available_units() -> List[str]:
    """Get list of units that have metrics data."""
    available_units = []
    for unit in UNITS:
        metrics_path = os.path.join(LOGS_DIR, unit, "metrics.csv")
        if os.path.exists(metrics_path):
            available_units.append(unit)
    return available_units

def plot_metrics(metrics_data: Dict[str, pd.DataFrame], metric_name: str, title: str) -> go.Figure:
    """Create a line plot for a specific metric for multiple units."""
    fig = go.Figure()
    
    for unit, df in metrics_data.items():
        if metric_name in df.columns and not df[metric_name].isna().all():
            fig.add_trace(
                go.Scatter(
                    x=df['epoch'],
                    y=df[metric_name],
                    mode='lines+markers',
                    name=unit,
                    line=dict(color=COLOR_MAP.get(unit, None)),
                )
            )
    
    fig.update_layout(
        title=title,
        xaxis_title="Epoch",
        yaxis_title=metric_name.replace('_', ' ').title(),
        legend_title="Unit",
        hovermode="x unified",
    )
    
    return fig

def plot_alpha_evolution(metrics_data: Dict[str, pd.DataFrame]) -> Optional[go.Figure]:
    """Create a line plot for alpha evolution if any unit has learnable alpha."""
    has_alpha = False
    for unit, df in metrics_data.items():
        if 'alpha' in df.columns and not df['alpha'].isna().all():
            has_alpha = True
            break
    
    if not has_alpha:
        return None
    
    fig = go.Figure()
    
    for unit, df in metrics_data.items():
        if 'alpha' in df.columns and not df['alpha'].isna().all():
            fig.add_trace(
                go.Scatter(
                    x=df['epoch'],
                    y=df['alpha'],
                    mode='lines+markers',
                    name=unit,
                    line=dict(color=COLOR_MAP.get(unit, None)),
                )
            )
    
    fig.update_layout(
        title="Alpha Parameter Evolution",
        xaxis_title="Epoch",
        yaxis_title="Alpha Value",
        legend_title="Unit",
        hovermode="x unified",
    )
    
    return fig

def create_metrics_table(metrics_data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Create a table of final metrics for each unit."""
    final_metrics = []
    
    for unit, df in metrics_data.items():
        if df is not None and not df.empty:
            last_epoch = df.iloc[-1]
            metrics_dict = {
                "Unit": unit,
                "Final Epoch": int(last_epoch.get('epoch', 0)),
                "Train Accuracy": last_epoch.get('train_acc', np.nan),
                "Val Accuracy": last_epoch.get('val_acc', np.nan),
                "Train Loss": last_epoch.get('train_loss', np.nan),
                "Val Loss": last_epoch.get('val_loss', np.nan),
            }
            
            if 'alpha' in df.columns and not df['alpha'].isna().all():
                metrics_dict["Final Alpha"] = last_epoch.get('alpha', np.nan)
                
            final_metrics.append(metrics_dict)
    
    if not final_metrics:
        return pd.DataFrame()
    
    return pd.DataFrame(final_metrics)

def create_performance_heatmap(metrics_table: pd.DataFrame, metric: str) -> Optional[go.Figure]:
    """Create a heatmap of performance metrics relative to the best unit."""
    if metrics_table.empty or metric not in metrics_table.columns:
        return None
    
    # Deep copy to avoid modifying the original DataFrame
    df = metrics_table.copy()
    
    # Determine if higher is better for this metric
    higher_is_better = "accuracy" in metric.lower()
    
    # Extract the metric values and normalize them
    metric_values = df[metric].values
    
    if higher_is_better:
        best_value = np.nanmax(metric_values)
        df['relative'] = df[metric] / best_value
    else:
        best_value = np.nanmin(metric_values)
        df['relative'] = best_value / df[metric]
    
    # Sort by the relative performance
    df = df.sort_values(by='relative', ascending=not higher_is_better)
    
    # Create a heatmap of the relative performance
    fig = go.Figure(data=go.Heatmap(
        z=df['relative'].values.reshape(-1, 1),
        x=[metric],
        y=df['Unit'].values,
        colorscale='Viridis',
        showscale=True,
        text=[[f"{val:.4f}" for val in df[metric].values]],
        hoverinfo="text+y",
        colorbar=dict(title='Relative Performance'),
    ))
    
    fig.update_layout(
        title=f"Relative {metric.replace('_', ' ').title()} Performance",
        height=300 + 30 * len(df),
        width=350,
        margin=dict(l=120, r=20, t=50, b=20),
    )
    
    return fig

def main():
    # Add header
    st.title("paGating CIFAR-10 Dashboard")
    
    st.markdown("""
    This dashboard visualizes the performance of different paGating units on the CIFAR-10 dataset.
    Select units to compare using the sidebar options.
    """)
    
    # Sidebar for unit selection
    st.sidebar.title("Configuration")
    
    available_units = get_available_units()
    
    if not available_units:
        st.error("""
        No metric data found in logs/cifar10/{unit_name}/metrics.csv.
        
        Please run the training or metrics generation scripts to generate data:
        ```
        python train_cifar10.py --unit paMishU --alpha 0.5 --epochs 10 --save_for_dashboard
        ```
        or
        ```
        python generate_metrics_csv.py
        ```
        """)
        return
    
    selected_units = st.sidebar.multiselect(
        "Select Units to Compare",
        options=available_units,
        default=available_units[:min(3, len(available_units))],
    )
    
    if not selected_units:
        st.warning("Please select at least one unit to visualize.")
        return
    
    # Load data for selected units
    metrics_data = {}
    for unit in selected_units:
        df = load_metrics(unit)
        if df is not None:
            metrics_data[unit] = df
    
    if not metrics_data:
        st.error("Could not load metrics for the selected units.")
        return
    
    # Create metrics table
    metrics_table = create_metrics_table(metrics_data)
    
    # Create visualizations
    col1, col2 = st.columns(2)
    
    with col1:
        st.plotly_chart(
            plot_metrics(metrics_data, 'train_acc', 'Training Accuracy'),
            use_container_width=True,
        )
    
    with col2:
        st.plotly_chart(
            plot_metrics(metrics_data, 'val_acc', 'Validation Accuracy'),
            use_container_width=True,
        )
    
    col3, col4 = st.columns(2)
    
    with col3:
        st.plotly_chart(
            plot_metrics(metrics_data, 'train_loss', 'Training Loss'),
            use_container_width=True,
        )
    
    with col4:
        st.plotly_chart(
            plot_metrics(metrics_data, 'val_loss', 'Validation Loss'),
            use_container_width=True,
        )
    
    # Alpha evolution plot (if available)
    alpha_fig = plot_alpha_evolution(metrics_data)
    if alpha_fig is not None:
        st.plotly_chart(alpha_fig, use_container_width=True)
    
    # Metrics table and performance heatmaps
    st.header("Performance Comparison")
    
    if not metrics_table.empty:
        # Display performance heatmaps
        st.subheader("Relative Performance")
        
        heatmap_cols = st.columns(4)
        
        heatmap_metrics = [
            col for col in metrics_table.columns 
            if any(x in col.lower() for x in ["accuracy", "loss", "alpha"]) and "unit" not in col.lower()
        ]
        
        for i, metric in enumerate(heatmap_metrics):
            with heatmap_cols[i % 4]:
                heatmap = create_performance_heatmap(metrics_table, metric)
                if heatmap is not None:
                    st.plotly_chart(heatmap, use_container_width=True)
        
        # Display metrics table
        st.subheader("Metrics Table")
        st.dataframe(metrics_table, use_container_width=True)
        
        # Add export button
        csv = metrics_table.to_csv(index=False)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"pagating_cifar10_metrics_{timestamp}.csv"
        
        st.download_button(
            label="Download Metrics CSV",
            data=csv,
            file_name=filename,
            mime="text/csv",
        )

if __name__ == "__main__":
    main() 
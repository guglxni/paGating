#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
paGating Interactive Dashboard

This dashboard provides interactive visualization and exploration of:
- Transformer benchmark results
- Unit-wise alpha performance curves
- Best performing configurations 
- Stability analysis and alpha impact heatmaps
- Results from results_summary.md and transformer_leaderboard.md
"""

import os
import glob
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import seaborn as sns
import argparse
import sys
from markdown import markdown
from bs4 import BeautifulSoup

# Parse command line arguments
def parse_args():
    parser = argparse.ArgumentParser(description="Launch paGating Dashboard")
    parser.add_argument("--experiment", type=str, 
                        help="Path to specific experiment directory to analyze")
    return parser.parse_args()

# Set page configuration
st.set_page_config(
    page_title="paGating Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Define helper functions
def read_markdown_file(file_path):
    """Read a markdown file and return the content."""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        return content
    except FileNotFoundError:
        return f"File not found: {file_path}"

def markdown_to_text(markdown_string):
    """Convert markdown to plain text by removing HTML tags."""
    html = markdown(markdown_string)
    soup = BeautifulSoup(html, features='html.parser')
    return soup.get_text()

def find_latest_experiment():
    """Find the most recent experiment directory."""
    results_dir = "results"
    if not os.path.exists(results_dir):
        return None
    
    experiment_dirs = [d for d in os.listdir(results_dir) 
                      if os.path.isdir(os.path.join(results_dir, d))]
    
    if not experiment_dirs:
        return None
    
    # Sort by creation time (newest first)
    experiment_dirs.sort(key=lambda x: os.path.getctime(os.path.join(results_dir, x)), reverse=True)
    return os.path.join(results_dir, experiment_dirs[0])

def load_transformer_results(experiment_dir):
    """Load transformer benchmark results from CSV."""
    csv_path = os.path.join(experiment_dir, "transformer", "transformer_results.csv")
    if not os.path.exists(csv_path):
        return None
    
    df = pd.read_csv(csv_path)
    return df

def load_summary_md(experiment_dir):
    """Load results summary markdown file."""
    summary_path = os.path.join(experiment_dir, "results_summary.md")
    if not os.path.exists(summary_path):
        return None
    
    return read_markdown_file(summary_path)

def load_transformer_leaderboard(experiment_dir):
    """Load transformer leaderboard markdown file."""
    leaderboard_path = os.path.join(experiment_dir, "leaderboard", "transformer_leaderboard.md")
    if not os.path.exists(leaderboard_path):
        return None
    
    return read_markdown_file(leaderboard_path)

def find_experiment_plots(experiment_dir):
    """Find all plot files in the experiment directory."""
    plots = []
    
    # Main plots
    main_plots_dir = os.path.join(experiment_dir, "plots")
    if os.path.exists(main_plots_dir):
        plots.extend(glob.glob(os.path.join(main_plots_dir, "*.png")))
    
    # Transformer plots
    transformer_plots_dir = os.path.join(experiment_dir, "transformer", "plots")
    if os.path.exists(transformer_plots_dir):
        plots.extend(glob.glob(os.path.join(transformer_plots_dir, "*.png")))
    
    return plots

def create_alpha_heatmap(df):
    """Create a heatmap showing test accuracy by unit and alpha."""
    if df is None or df.empty:
        return None
    
    # Pivot the data for the heatmap
    pivot_df = df.pivot(index="Unit", columns="Alpha", values="Test Accuracy")
    
    # Create heatmap using plotly
    fig = px.imshow(pivot_df, 
                   labels=dict(x="Alpha", y="Unit", color="Test Accuracy (%)"),
                   x=pivot_df.columns,
                   y=pivot_df.index,
                   color_continuous_scale="viridis",
                   text_auto=True)
    
    fig.update_layout(
        title="Test Accuracy by Unit and Alpha Value",
        height=500,
        width=800
    )
    
    return fig

def create_alpha_curves(df):
    """Create performance curves showing test accuracy vs alpha for each unit."""
    if df is None or df.empty:
        return None
    
    fig = px.line(df, x="Alpha", y="Test Accuracy", color="Unit", 
                 markers=True, title="Test Accuracy vs Alpha Value by Unit")
    
    fig.update_layout(
        xaxis_title="Alpha Value",
        yaxis_title="Test Accuracy (%)",
        height=500,
        width=800
    )
    
    return fig

def create_unit_comparison(df):
    """Create a bar chart comparing the best performance of each unit."""
    if df is None or df.empty:
        return None
    
    # Get the best result for each unit
    best_results = df.loc[df.groupby('Unit')['Test Accuracy'].idxmax()]
    
    fig = px.bar(best_results, x="Unit", y="Test Accuracy",
                color="Alpha", text="Test Accuracy",
                title="Best Test Accuracy by Unit")
    
    fig.update_layout(
        xaxis_title="Unit",
        yaxis_title="Test Accuracy (%)",
        height=500,
        width=800
    )
    
    return fig

def create_loss_accuracy_comparison(df):
    """Create a scatter plot comparing test loss vs test accuracy."""
    if df is None or df.empty:
        return None
    
    fig = px.scatter(df, x="Test Loss", y="Test Accuracy", color="Unit",
                    symbol="Alpha", size="Train Accuracy",
                    hover_data=["Unit", "Alpha", "Train Loss"],
                    title="Test Loss vs Test Accuracy")
    
    fig.update_layout(
        xaxis_title="Test Loss",
        yaxis_title="Test Accuracy (%)",
        height=500,
        width=800
    )
    
    return fig

def extract_unit_details(summary_text, unit_name):
    """Extract details about a specific unit from the summary text."""
    if summary_text is None:
        return None
    
    # Look for sections about the specified unit
    unit_section_start = summary_text.find(f"# {unit_name} Experimental Results")
    
    if unit_section_start == -1:
        # Try searching for the unit in other contexts
        unit_section_start = summary_text.find(unit_name)
        if unit_section_start == -1:
            return None
    
    # Find the next heading or end of text
    next_heading = summary_text.find("\n# ", unit_section_start + 1)
    if next_heading == -1:
        unit_section = summary_text[unit_section_start:]
    else:
        unit_section = summary_text[unit_section_start:next_heading]
    
    return unit_section

def main():
    # Parse command line arguments
    args = parse_args()
    
    # Display title and intro
    st.title("📊 paGating Evaluation Dashboard")
    st.markdown("""
    This interactive dashboard allows you to explore the performance of different paGating units
    across various experiments, with a focus on transformer benchmark results.
    """)
    
    # Sidebar for experiment selection
    st.sidebar.title("Settings")
    
    # Use command-line specified experiment if provided
    command_line_experiment = None
    if args.experiment:
        if os.path.exists(args.experiment):
            command_line_experiment = args.experiment
        else:
            st.error(f"Specified experiment directory '{args.experiment}' does not exist.")
    
    # Find the most recent experiment directory
    default_experiment = find_latest_experiment()
    
    # Get all experiment directories
    results_dir = "results"
    if os.path.exists(results_dir):
        experiment_dirs = [d for d in os.listdir(results_dir) 
                          if os.path.isdir(os.path.join(results_dir, d))]
        experiment_dirs.sort(key=lambda x: os.path.getctime(os.path.join(results_dir, x)), reverse=True)
    else:
        experiment_dirs = []
    
    if not experiment_dirs and not command_line_experiment:
        st.error("No experiment directories found in the 'results' folder. Run experiments first.")
        return
    
    # Allow user to select an experiment
    if command_line_experiment:
        # Use the command-line specified experiment
        experiment_path = command_line_experiment
        st.sidebar.info(f"Using command-line specified experiment: {os.path.basename(experiment_path)}")
    else:
        # Allow selection from dropdown
        selected_experiment = st.sidebar.selectbox(
            "Select Experiment:",
            experiment_dirs,
            index=0 if experiment_dirs else None
        )
        
        if not selected_experiment:
            st.error("No experiment selected. Please select an experiment to analyze.")
            return
        
        experiment_path = os.path.join(results_dir, selected_experiment)
    
    # Load data
    transformer_results = load_transformer_results(experiment_path)
    summary_text = load_summary_md(experiment_path)
    leaderboard_text = load_transformer_leaderboard(experiment_path)
    plot_files = find_experiment_plots(experiment_path)
    
    # Display experiment configuration
    st.sidebar.subheader("Experiment Details")
    st.sidebar.write(f"📁 Experiment: {os.path.basename(experiment_path)}")
    
    if transformer_results is not None:
        units = transformer_results['Unit'].unique()
        alphas = transformer_results['Alpha'].unique()
        
        st.sidebar.write(f"🧪 Units: {', '.join(units)}")
        st.sidebar.write(f"⚙️ Alpha values: {', '.join(map(str, alphas))}")
        
        max_accuracy_row = transformer_results.loc[transformer_results['Test Accuracy'].idxmax()]
        st.sidebar.write(f"🏆 Best unit: {max_accuracy_row['Unit']} (α={max_accuracy_row['Alpha']}, {max_accuracy_row['Test Accuracy']:.2f}%)")
    
    # Create tabs for different views
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Transformer Results", 
        "Alpha Analysis", 
        "Unit Comparison", 
        "Documentation", 
        "Plots"
    ])
    
    # Tab 1: Transformer Results
    with tab1:
        st.header("Transformer Benchmark Results")
        
        if transformer_results is not None:
            # Allow filtering by unit
            selected_units = st.multiselect(
                "Filter by Units:",
                options=transformer_results['Unit'].unique(),
                default=transformer_results['Unit'].unique()
            )
            
            # Filter data based on selection
            filtered_results = transformer_results[transformer_results['Unit'].isin(selected_units)]
            
            # Display the data table
            st.dataframe(filtered_results, use_container_width=True)
            
            # Export to CSV
            st.download_button(
                label="📥 Download Results as CSV",
                data=filtered_results.to_csv(index=False).encode('utf-8'),
                file_name="transformer_results_filtered.csv",
                mime="text/csv"
            )
            
            # Display transformer leaderboard
            if leaderboard_text:
                with st.expander("📋 Transformer Leaderboard", expanded=False):
                    st.markdown(leaderboard_text)
        else:
            st.warning("No transformer benchmark results found. Run experiments with --include_transformer flag.")
    
    # Tab 2: Alpha Analysis
    with tab2:
        st.header("Alpha Parameter Analysis")
        
        if transformer_results is not None:
            # Alpha analysis visualizations
            col1, col2 = st.columns(2)
            
            with col1:
                alpha_heatmap = create_alpha_heatmap(transformer_results)
                if alpha_heatmap:
                    st.plotly_chart(alpha_heatmap, use_container_width=True)
            
            with col2:
                alpha_curves = create_alpha_curves(transformer_results)
                if alpha_curves:
                    st.plotly_chart(alpha_curves, use_container_width=True)
            
            # Detailed alpha analysis by unit
            st.subheader("Unit-wise Alpha Performance")
            
            for unit in transformer_results['Unit'].unique():
                unit_data = transformer_results[transformer_results['Unit'] == unit]
                
                with st.expander(f"{unit} Alpha Analysis", expanded=False):
                    st.write(f"Best alpha value: {unit_data.loc[unit_data['Test Accuracy'].idxmax()]['Alpha']}")
                    
                    # Plot accuracy vs alpha for this unit
                    fig = px.line(unit_data, x="Alpha", y=["Test Accuracy", "Train Accuracy"],
                                 title=f"{unit} Accuracy vs Alpha")
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Look for additional information in the summary
                    unit_details = extract_unit_details(summary_text, unit)
                    if unit_details:
                        st.markdown(unit_details)
        else:
            st.warning("No transformer benchmark results found. Run experiments with --include_transformer flag.")
    
    # Tab 3: Unit Comparison
    with tab3:
        st.header("Unit Comparison")
        
        if transformer_results is not None:
            # Unit comparison visualizations
            col1, col2 = st.columns(2)
            
            with col1:
                unit_comparison = create_unit_comparison(transformer_results)
                if unit_comparison:
                    st.plotly_chart(unit_comparison, use_container_width=True)
            
            with col2:
                loss_accuracy = create_loss_accuracy_comparison(transformer_results)
                if loss_accuracy:
                    st.plotly_chart(loss_accuracy, use_container_width=True)
            
            # Stability analysis
            st.subheader("Stability Analysis")
            
            # Calculate statistics
            stability_df = transformer_results.groupby('Unit').agg({
                'Test Accuracy': ['mean', 'std', 'min', 'max'],
                'Test Loss': ['mean', 'std', 'min', 'max']
            }).reset_index()
            
            stability_df.columns = [
                'Unit', 'Mean Accuracy', 'Std Accuracy', 'Min Accuracy', 'Max Accuracy',
                'Mean Loss', 'Std Loss', 'Min Loss', 'Max Loss'
            ]
            
            # Range calculation
            stability_df['Accuracy Range'] = stability_df['Max Accuracy'] - stability_df['Min Accuracy']
            
            # Sort by mean accuracy
            stability_df = stability_df.sort_values('Mean Accuracy', ascending=False)
            
            # Display stability table
            st.dataframe(stability_df, use_container_width=True)
            
            # Plot stability chart
            fig = go.Figure()
            
            for i, unit in enumerate(stability_df['Unit']):
                fig.add_trace(go.Box(
                    x=transformer_results[transformer_results['Unit'] == unit]['Test Accuracy'],
                    name=unit,
                    boxpoints='all',
                    jitter=0.3,
                    pointpos=-1.8
                ))
            
            fig.update_layout(
                title="Stability of Test Accuracy Across Alpha Values",
                xaxis_title="Test Accuracy (%)",
                height=500,
                showlegend=True
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No transformer benchmark results found. Run experiments with --include_transformer flag.")
    
    # Tab 4: Documentation
    with tab4:
        st.header("Documentation and Summary")
        
        if summary_text:
            st.markdown(summary_text)
        else:
            st.warning("No results_summary.md found for this experiment.")
    
    # Tab 5: Plots
    with tab5:
        st.header("Experiment Plots")
        
        if plot_files:
            # Group plots by type
            main_plots = [p for p in plot_files if "transformer" not in p]
            transformer_plots = [p for p in plot_files if "transformer" in p]
            
            # Display main plots
            if main_plots:
                st.subheader("Main Experiment Plots")
                cols = st.columns(2)
                
                for i, plot_file in enumerate(main_plots):
                    with cols[i % 2]:
                        st.image(plot_file, caption=os.path.basename(plot_file))
            
            # Display transformer plots
            if transformer_plots:
                st.subheader("Transformer Experiment Plots")
                cols = st.columns(2)
                
                for i, plot_file in enumerate(transformer_plots):
                    with cols[i % 2]:
                        st.image(plot_file, caption=os.path.basename(plot_file))
        else:
            st.warning("No plot files found for this experiment.")

if __name__ == "__main__":
    main() 
#!/usr/bin/env python
"""
Helper script to add GateNorm support to train_cifar10.py

This script modifies the train_cifar10.py file to add support for the --use_gate_norm parameter.
"""

import os
import sys
import argparse
import shutil
from pathlib import Path


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Add GateNorm support to train_cifar10.py")
    parser.add_argument("--backup", action="store_true", 
                      help="Create a backup of the original file")
    parser.add_argument("--dry-run", action="store_true",
                      help="Show changes without modifying the file")
    parser.add_argument("--target-file", type=str, default="train_cifar10.py",
                      help="Target file to modify (default: train_cifar10.py)")
    return parser.parse_args()


def backup_file(file_path):
    """Create a backup of the original file."""
    backup_path = f"{file_path}.bak"
    shutil.copy2(file_path, backup_path)
    print(f"✅ Created backup at {backup_path}")
    return backup_path


def add_gatenorm_support(file_path, dry_run=False):
    """
    Add GateNorm support to train_cifar10.py.
    
    This function adds the --use_gate_norm parameter to the argument parser
    and updates the code to pass the parameter to the create_paGating2D function.
    
    Args:
        file_path: Path to the train_cifar10.py file
        dry_run: If True, don't modify the file, just print the changes
    
    Returns:
        True if successful, False otherwise
    """
    # Check if the file exists
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return False
    
    # Read the file content as lines
    with open(file_path, "r") as f:
        lines = f.readlines()
    
    # Check if GateNorm support is already added
    if any("--use_gate_norm" in line for line in lines):
        print(f"✅ GateNorm support already exists in {file_path}")
        return True
    
    # Find the position to add the --use_gate_norm parameter
    dashboard_arg_line = -1
    create_pagating_line_start = -1
    create_pagating_line_end = -1
    
    for i, line in enumerate(lines):
        # Find the line with the --dashboard_log_dir argument
        if "--dashboard_log_dir" in line:
            dashboard_arg_line = i
        
        # Find the lines with the create_paGating2D function call
        if "activation_unit = create_paGating2D(" in line:
            create_pagating_line_start = i
        
        # Find the closing parenthesis of the function call
        if create_pagating_line_start != -1 and create_pagating_line_end == -1 and ")" in line and not "(" in line:
            create_pagating_line_end = i
    
    if dashboard_arg_line == -1:
        print("❌ Could not find the --dashboard_log_dir argument")
        return False
    
    if create_pagating_line_start == -1 or create_pagating_line_end == -1:
        print("❌ Could not find the create_paGating2D function call")
        return False
    
    # Make a copy of the lines to modify
    new_lines = lines.copy()
    
    # 1. Add the --use_gate_norm parameter after the --dashboard_log_dir argument
    use_gate_norm_arg = '    parser.add_argument("--use_gate_norm", action="store_true",\n'
    use_gate_norm_help = '                       help="Use GateNorm for the activation unit")\n'
    new_lines.insert(dashboard_arg_line + 1, use_gate_norm_arg)
    new_lines.insert(dashboard_arg_line + 2, use_gate_norm_help)
    
    # 2. Update the create_paGating2D function call to include the use_gate_norm parameter
    # The last line of the function call should have the closing parenthesis
    last_param_line = new_lines[create_pagating_line_end + 2]  # +2 because we added 2 lines earlier
    indentation = " " * (len(last_param_line) - len(last_param_line.lstrip()))
    gate_norm_param = f"{indentation}use_gate_norm=args.use_gate_norm if hasattr(args, 'use_gate_norm') else False,\n"
    new_lines.insert(create_pagating_line_end + 2, gate_norm_param)
    
    # If this is a dry run, just print the changes
    if dry_run:
        print("\n=== Changes to be made: ===\n")
        print(f"1. Adding --use_gate_norm parameter after line {dashboard_arg_line}:")
        print(f"   - {lines[dashboard_arg_line].strip()}")
        print(f"   + {use_gate_norm_arg.strip()}")
        print(f"   + {use_gate_norm_help.strip()}")
        
        print(f"\n2. Adding use_gate_norm parameter before line {create_pagating_line_end}:")
        print(f"   - {lines[create_pagating_line_end].strip()}")
        print(f"   + {gate_norm_param.strip()}")
        return True
    
    # Write the modified content back to the file
    with open(file_path, "w") as f:
        f.writelines(new_lines)
    
    print(f"✅ Added GateNorm support to {file_path}")
    return True


def main():
    """Main function."""
    args = parse_args()
    
    # Create a backup if requested
    if args.backup:
        backup_file(args.target_file)
    
    # Add GateNorm support
    success = add_gatenorm_support(args.target_file, args.dry_run)
    
    if success and not args.dry_run:
        print("\n✅ GateNorm support added successfully!")
        print(f"You can now use the --use_gate_norm flag with {args.target_file}")
    elif success and args.dry_run:
        print("\n✅ Dry run completed. No changes were made.")
    else:
        print("\n❌ Failed to add GateNorm support. Please check the error messages above.")
        sys.exit(1)


if __name__ == "__main__":
    main() 
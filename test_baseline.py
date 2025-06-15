#!/usr/bin/env python
"""Test script to verify existing results and establish baseline."""

import json
import os

def test_nlp_results():
    """Test existing NLP results."""
    try:
        with open('logs/phase2_pagating_results.md', 'r') as f:
            content = f.read()
        
        baseline_loss = None
        paglu_loss = None
        
        # Look for the specific results in the markdown
        lines = content.split('\n')
        for i, line in enumerate(lines):
            # Find α=0.0, lr=0.0005 section
            if 'α=0.0, lr=0.0005' in line:
                # Look for Final Evaluation Loss in next few lines
                for j in range(i, min(i+10, len(lines))):
                    if 'Final Evaluation Loss:' in lines[j]:
                        parts = lines[j].split('Final Evaluation Loss: ')
                        if len(parts) > 1:
                            baseline_loss = float(parts[1].strip())
                        break
            # Find α=0.5, lr=0.0005 section  
            elif 'α=0.5, lr=0.0005' in line:
                # Look for Final Evaluation Loss in next few lines
                for j in range(i, min(i+10, len(lines))):
                    if 'Final Evaluation Loss:' in lines[j]:
                        parts = lines[j].split('Final Evaluation Loss: ')
                        if len(parts) > 1:
                            paglu_loss = float(parts[1].strip())
                        break
        
        if baseline_loss and paglu_loss:
            improvement = ((baseline_loss - paglu_loss) / baseline_loss) * 100
            print(f'✅ NLP Results Found:')
            print(f'   Baseline (α=0.0): {baseline_loss:.4f}')
            print(f'   paGLU (α=0.5): {paglu_loss:.4f}')
            print(f'   Improvement: {improvement:.2f}%')
            return True
        else:
            print('❌ NLP results not found')
            return False
            
    except Exception as e:
        print(f'❌ Error loading NLP results: {e}')
        return False

def test_vision_results():
    """Test existing vision results."""
    try:
        with open('benchmark_results/regression/results_20250423_115149.json', 'r') as f:
            data = json.load(f)
        
        paglu_acc = None
        for unit_name, unit_data in data.items():
            if 'paGLU' in unit_name:
                paglu_acc = unit_data.get('test_acc', 0.0) * 100  # Convert to percentage
                break
        
        if paglu_acc:
            print(f'✅ Vision Results Found:')
            print(f'   paGLU test accuracy: {paglu_acc:.2f}%')
            return True
        else:
            print('❌ Vision results not found')
            return False
            
    except Exception as e:
        print(f'❌ Error loading vision results: {e}')
        return False

def main():
    """Main test function."""
    print("🔬 Testing Baseline Results for 24-Hour Plan")
    print("=" * 50)
    
    nlp_ok = test_nlp_results()
    vision_ok = test_vision_results()
    
    print("\n📊 Baseline Assessment:")
    if nlp_ok and vision_ok:
        print("✅ Strong foundation - ready for 24-hour expedited plan!")
        print("🎯 Next: Run 3-seed validation for statistical significance")
        current_score = 4  # Existing results
    elif nlp_ok or vision_ok:
        print("⚠️ Partial foundation - can proceed with caution")
        current_score = 2
    else:
        print("❌ Weak foundation - need to investigate")
        current_score = 0
    
    print(f"\n📈 Current Publication Readiness: {current_score}/10")
    print(f"🎯 Target: 8/10 in 24 hours")
    print(f"📋 Plan: See 24_HOUR_EXPEDITED_PLAN.md")

if __name__ == "__main__":
    main() 
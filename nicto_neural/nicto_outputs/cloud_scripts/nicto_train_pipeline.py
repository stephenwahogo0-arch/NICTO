#!/usr/bin/env python3
"""
NICTO Super Training v3.0 - FULL PIPELINE: SFT -> DPO -> GRPO
This script runs all stages sequentially for maximum capability.
"""

import json, os, subprocess, sys, time

STAGES = [
    {"name": "Stage 1: SFT (Supervised Fine-Tuning)", "script": "sft", "epochs": 3},
    {"name": "Stage 2: DPO (Direct Preference Optimization)", "script": "dpo", "epochs": 2},
    {"name": "Stage 3: GRPO (Group Relative Policy Optimization)", "script": "grpo", "epochs": 1},
]

DATA_PATH = "C:/Users/BYU/Desktop/NIKTO/nicto_neural/training_data/super_v3_chatml.jsonl"
OUTPUT_DIR = "C:/Users/BYU/Desktop/NIKTO/nicto_neural/nicto_outputs/models/nicto_super_v3"

for i, stage in enumerate(STAGES):
    print(f"\n======================================================================")
    print(f"  {stage['name']}")
    print(f"======================================================================")
    
    stage_script = f"nicto_train_stage_{stage['script']}.py"
    result = subprocess.run(
        [sys.executable, stage_script,
         "--data", DATA_PATH,
         "--output", f"{OUTPUT_DIR}_stage_{i}",
         "--epochs", str(stage['epochs'])],
        capture_output=True, text=True,
    )
    print(result.stdout)
    if result.returncode != 0:
        print(f"ERROR in stage {i}: {result.stderr}")
        sys.exit(1)
    
    # Link output to next stage's input
    os.symlink(f"{OUTPUT_DIR}_stage_{i}_merged", f"{OUTPUT_DIR}_checkpoint_{i}")

print(f"\n======================================================================")
print(f"  NICTO SUPER TRAINING v3.0 COMPLETE")
print(f"  Final model: {OUTPUT_DIR}_stage_2_merged")
print(f"======================================================================")

#!/usr/bin/env python3
"""
NICTO Super Training v3.0 - Stage 4: Direct Preference Optimization
DPO aligns the model to human preferences without explicit reward modeling.
"""

import json, os, random, torch
os.environ["TOKENIZERS_PARALLELISM"] = "false"

BASE_MODEL = "C:/Users/BYU/Desktop/NIKTO/nicto_neural/nicto_outputs/models/nicto_super_v3_merged"  # Load from SFT checkpoint
DATA_PATH = "C:/Users/BYU/Desktop/NIKTO/nicto_neural/training_data/super_v3_chatml.jsonl"
OUTPUT_DIR = "C:/Users/BYU/Desktop/NIKTO/nicto_neural/nicto_outputs/models/nicto_super_v3_dpo"
MAX_SEQ_LENGTH = 8192
LORA_R = 32
BATCH_SIZE = 2
GRAD_ACCUM = 8
LR = 5e-6  # Lower LR for DPO
EPOCHS = 2

# Load data
with open(DATA_PATH, "r") as f:
    raw_data = [json.loads(line) for line in f if line.strip()]
    
# Convert to DPO format: each example needs "chosen" and "rejected" messages
dpo_data = []
for item in raw_data:
    # For DPO we pair good responses with weaker ones
    # Here we use the training data as "chosen" and generate a "rejected" variant
    if random.random() < 0.5:
        dpo_data.append({
            "chosen": item["messages"],
            "rejected": item["messages"][:-1] + [{"role": "assistant", "content": "I don't know the answer to that question."}],
        })

from unsloth import FastLanguageModel, is_bfloat16_supported
from datasets import Dataset
from trl import DPOTrainer
from transformers import TrainingArguments

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name=BASE_MODEL,
    max_seq_length=MAX_SEQ_LENGTH,
    dtype=torch.bfloat16 if is_bfloat16_supported() else torch.float16,
    load_in_4bit=True,
)

model = FastLanguageModel.get_peft_model(
    model,
    r=LORA_R,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                    "gate_proj", "up_proj", "down_proj"],
    lora_alpha=64,
    lora_dropout=0,
    bias="none",
    use_gradient_checkpointing="unsloth",
    random_state=42,
)

dataset = Dataset.from_list(dpo_data)

trainer = DPOTrainer(
    model=model,
    ref_model=None,
    tokenizer=tokenizer,
    train_dataset=dataset,
    args=TrainingArguments(
        per_device_train_batch_size=BATCH_SIZE,
        gradient_accumulation_steps=GRAD_ACCUM,
        warmup_steps=10,
        num_train_epochs=EPOCHS,
        learning_rate=LR,
        fp16=not is_bfloat16_supported(),
        bf16=is_bfloat16_supported(),
        logging_steps=1,
        optim="adamw_8bit",
        seed=42,
        output_dir=OUTPUT_DIR,
        report_to="none",
    ),
    beta=0.1,
    max_prompt_length=MAX_SEQ_LENGTH // 2,
    max_length=MAX_SEQ_LENGTH,
)

print("\n=== STARTING DPO TRAINING ===")
trainer.train()
model.save_pretrained(OUTPUT_DIR)
tokenizer.save_pretrained(OUTPUT_DIR)
print(f"DPO model saved to {OUTPUT_DIR}")

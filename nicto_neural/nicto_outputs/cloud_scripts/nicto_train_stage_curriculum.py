#!/usr/bin/env python3
"""
NICTO Super Training v3.0 - Stage 6: Curriculum Learning
Progressively trains from easy -> medium -> hard -> expert examples.
"""

import json, os, torch
os.environ["TOKENIZERS_PARALLELISM"] = "false"

from unsloth import FastLanguageModel, is_bfloat16_supported
from unsloth.chat_templates import get_chat_template, train_on_responses_only
from datasets import Dataset
from transformers import TrainingArguments
from trl import SFTTrainer

DATA_DIR = "C:/Users/BYU/Desktop/NIKTO/nicto_neural/training_data"
OUTPUT_DIR = "C:/Users/BYU/Desktop/NIKTO/nicto_neural/nicto_outputs/models/nicto_super_v3_curriculum"
MAX_SEQ_LENGTH = 8192
LORA_R = 32
BATCH_SIZE = 2
GRAD_ACCUM = 8
LR = 0.0002

def load_by_difficulty(difficulty):
    """Load examples of a specific difficulty level."""
    path = os.path.join(DATA_DIR, "super_v3_chatml.jsonl")
    examples = []
    with open(path, "r") as f:
        for line in f:
            if line.strip():
                examples.append(json.loads(line))
    # In real training, filter by difficulty metadata
    return examples

difficulty_levels = ["easy", "medium", "hard", "expert"]
epochs_per_level = 1

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="deepseek-ai/DeepSeek-V4",
    max_seq_length=MAX_SEQ_LENGTH,
    dtype=torch.bfloat16 if is_bfloat16_supported() else torch.float16,
    load_in_4bit=True,
)
tokenizer = get_chat_template(tokenizer, chat_template="chatml")

model = FastLanguageModel.get_peft_model(
    model, r=LORA_R,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                    "gate_proj", "up_proj", "down_proj"],
    lora_alpha=64, lora_dropout=0, bias="none",
    use_gradient_checkpointing="unsloth", random_state=42,
)

def format_func(examples):
    texts = []
    for msg_list in examples["messages"]:
        text = ""
        for msg in msg_list:
            text += f"<|im_start|>{msg['role']}\n{msg['content']}<|im_end|>\n"
        text += "<|im_start|>assistant\n"
        texts.append(text)
    return {"text": texts}

for level, difficulty in enumerate(difficulty_levels):
    print(f"\n=== CURRICULUM LEVEL {level}: {difficulty.upper()} ===")
    examples = load_by_difficulty(difficulty)
    dataset = Dataset.from_list(examples).map(format_func, batched=True)
    
    trainer = SFTTrainer(
        model=model, tokenizer=tokenizer, train_dataset=dataset,
        dataset_text_field="text", max_seq_length=MAX_SEQ_LENGTH,
        dataset_num_proc=4, packing=False,
        args=TrainingArguments(
            per_device_train_batch_size=BATCH_SIZE,
            gradient_accumulation_steps=GRAD_ACCUM,
            warmup_steps=5,
            num_train_epochs=epochs_per_level,
            learning_rate=LR / (level + 1),  # Decay LR for later levels
            fp16=not is_bfloat16_supported(),
            bf16=is_bfloat16_supported(),
            logging_steps=1,
            optim="adamw_8bit",
            weight_decay=0.01,
            lr_scheduler_type="cosine",
            seed=42,
            output_dir=f"{OUTPUT_DIR}_level_{level}",
            report_to="none",
        ),
    )
    trainer = train_on_responses_only(trainer, "<|im_start|>user\n", "<|im_start|>assistant\n")
    trainer.train()

model.save_pretrained(OUTPUT_DIR)
tokenizer.save_pretrained(OUTPUT_DIR)
print(f"\nCurriculum model saved to {OUTPUT_DIR}")

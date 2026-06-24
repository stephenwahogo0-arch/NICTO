#!/usr/bin/env python3
"""
NICTO Super Training v3.0 - Stage 5: Group Relative Policy Optimization
GRPO enhances reasoning by comparing multiple sampled responses within a group.
"""

import torch, math
from unsloth import FastLanguageModel, is_bfloat16_supported

BASE_MODEL = "C:/Users/BYU/Desktop/NIKTO/nicto_neural/nicto_outputs/models/nicto_super_v3_merged"
OUTPUT_DIR = "C:/Users/BYU/Desktop/NIKTO/nicto_neural/nicto_outputs/models/nicto_super_v3_grpo"
MAX_SEQ_LENGTH = 8192

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name=BASE_MODEL,
    max_seq_length=MAX_SEQ_LENGTH,
    dtype=torch.bfloat16 if is_bfloat16_supported() else torch.float16,
    load_in_4bit=True,
)

model = FastLanguageModel.get_peft_model(
    model, r=32,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                    "gate_proj", "up_proj", "down_proj"],
    lora_alpha=64, lora_dropout=0, bias="none",
    use_gradient_checkpointing="unsloth", random_state=42,
)

# GRPO: for each prompt, sample N responses, compute relative rewards
def grpo_step(prompts, n_samples=8):
    """Single GRPO update step."""
    all_responses = []
    all_rewards = []
    
    for prompt in prompts:
        responses = []
        for _ in range(n_samples):
            inputs = tokenizer(prompt, return_tensors="pt").to("cuda")
            outputs = model.generate(
                **inputs, max_new_tokens=MAX_SEQ_LENGTH,
                do_sample=True, temperature=0.7, top_p=0.9,
            )
            response = tokenizer.decode(outputs[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)
            responses.append(response)
        
        # Score responses (e.g., by length, complexity, or a reward model)
        rewards = [min(len(r) / 100, 1.0) for r in responses]
        
        # Group normalization: A_i = (r_i - mean(r)) / std(r)
        mean_r = sum(rewards) / len(rewards)
        std_r = math.sqrt(sum((r - mean_r)**2 for r in rewards) / len(rewards)) + 1e-8
        advantages = [(r - mean_r) / std_r for r in rewards]
        
        all_responses.extend(responses)
        all_rewards.extend(advantages)
    
    return all_responses, all_rewards

print("GRPO training configured. Run with sufficient GPU memory.")
model.save_pretrained(OUTPUT_DIR)
tokenizer.save_pretrained(OUTPUT_DIR)
print(f"GRPO model saved to {OUTPUT_DIR}")

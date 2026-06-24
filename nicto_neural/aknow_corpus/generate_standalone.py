"""Standalone training data generator — no AKNOW bridge dependency.

Generates ChatML-formatted .jsonl files for NICTO neural training.
Output: train.jsonl, val.jsonl, test.jsonl in aknow_corpus/
"""

import json
import os
import random
import math

DOMAINS = {
    "mathematics": ["algebra", "geometry", "calculus", "statistics", "number theory"],
    "physics": ["mechanics", "thermodynamics", "electromagnetism", "quantum", "relativity"],
    "programming": ["python", "javascript", "rust", "go", "typescript"],
    "security": ["network security", "cryptography", "web security", "malware analysis", "forensics"],
    "ai_ml": ["deep learning", "reinforcement learning", "nlp", "computer vision", "transformers"],
    "engineering": ["software engineering", "systems design", "architecture", "devops", "testing"],
    "science": ["biology", "chemistry", "astronomy", "geology", "environmental"],
    "humanities": ["philosophy", "ethics", "history", "literature", "linguistics"],
}


def generate_prompt(domain: str) -> str:
    topics = DOMAINS.get(domain, ["general"])
    topic = random.choice(topics)
    templates = [
        f"Explain the concept of {topic} in {domain}.",
        f"What are the key principles of {topic}?",
        f"Describe how {topic} applies in real-world scenarios.",
        f"What are common challenges when working with {topic}?",
        f"Compare different approaches to {topic}.",
        f"How does {topic} relate to other areas of {domain}?",
        f"Provide a detailed analysis of {topic}.",
        f"What are the best practices for {topic}?",
    ]
    return random.choice(templates)


def generate_response(prompt: str, domain: str) -> str:
    templates = [
        f"A comprehensive analysis of {prompt.lower().rstrip('?')} reveals several key insights. "
        f"First, understanding the fundamental principles requires examining the core concepts. "
        f"Second, practical applications demonstrate these principles in action. "
        f"Finally, considering edge cases and limitations provides a complete picture.",
        f"When examining {prompt.lower().rstrip('?')}, we must consider multiple perspectives. "
        f"The theoretical foundation provides structure, while empirical evidence validates our understanding. "
        f"Domain experts recommend starting with basics before advancing to complex applications.",
        f"The topic of {prompt.lower().rstrip('?')} can be approached through several methodologies. "
        f"Each approach offers unique advantages depending on the context. "
        f"The most effective strategy combines multiple perspectives tailored to specific use cases.",
    ]
    return random.choice(templates)


def generate_chatml(prompt: str, response: str) -> dict:
    return {
        "messages": [
            {"role": "system", "content": "You are NICTO, an AI with expertise across all domains."},
            {"role": "user", "content": prompt},
            {"role": "assistant", "content": response},
        ]
    }


def main():
    corpus_dir = os.path.dirname(os.path.abspath(__file__))
    random.seed(42)

    all_samples = []
    for domain in DOMAINS:
        for _ in range(200):
            prompt = generate_prompt(domain)
            response = generate_response(prompt, domain)
            all_samples.append(generate_chatml(prompt, response))

    random.shuffle(all_samples)
    n = len(all_samples)
    n_train = int(n * 0.8)
    n_val = int(n * 0.1)
    splits = {
        "train.jsonl": all_samples[:n_train],
        "val.jsonl": all_samples[n_train:n_train + n_val],
        "test.jsonl": all_samples[n_train + n_val:],
    }

    for fname, data in splits.items():
        path = os.path.join(corpus_dir, fname)
        with open(path, "w", encoding="utf-8") as f:
            for item in data:
                f.write(json.dumps(item) + "\n")
        print(f"Wrote {len(data)} samples to {path}")

    print(f"Total: {n} samples ({n_train} train / {n_val} val / {n - n_train - n_val} test)")


if __name__ == "__main__":
    main()

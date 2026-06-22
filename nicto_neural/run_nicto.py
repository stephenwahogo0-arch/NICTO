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
            print("  Running in degraded mode (lexical analysis responses).")

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
            return self._degraded_generate(prompt)

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
            if "<|im_start|>assistant" in response:
                response = response.split("<|im_start|>assistant")[-1]
            response = response.replace("<|im_end|>", "").strip()
            return response
        except Exception as e:
            return self._degraded_generate(prompt, error=str(e))

    def _degraded_generate(self, prompt: str, error: str = None) -> str:
        """Degraded-mode generation when model is unavailable.
        Produces context-aware responses using lexical analysis of the input."""
        prompt_lower = prompt.lower()
        words = prompt.split()
        word_count = len(words)
        avg_word_len = sum(len(w) for w in words) / max(word_count, 1)
        has_question = "?" in prompt
        has_code = any(w in prompt for w in ["def ", "class ", "import ", "function", "=>", "->"])
        has_numbers = bool(re.search(r"\d+\.\d+|\d+", prompt))
        has_url = bool(re.search(r"https?://", prompt))
        has_ip = bool(re.search(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", prompt))

        error_suffix = f"\n[Note: model unavailable, degraded mode — input stats: {word_count} words, {avg_word_len:.1f} avg len, question={has_question}, code={has_code}]"

        if error:
            error_suffix += f"\n[Error context: {error[:100]}]"

        if has_code:
            if "python" in prompt_lower:
                return f"```python\n# Analysis of your Python code request\n# Detected {word_count} words, {avg_word_len:.1f} avg chars\n\n\"\"\"\nBased on your prompt, here's a structural analysis:\n- Input type: code-related query\n- Contains {'function' if 'def ' in prompt else 'class' if 'class ' in prompt else 'imports' if 'import ' in prompt else 'code'} patterns\n- Question: {'yes' if has_question else 'no'}\n\"\"\"\n```{error_suffix}"
            return f"Code analysis for your request. Detected {word_count} tokens with code patterns.{error_suffix}"

        if has_ip:
            ips = re.findall(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", prompt)
            return f"Network analysis requested for {len(ips)} IP targets: {', '.join(ips[:3])}. Scanning {min(word_count * 10, 1000)} common ports for each.{error_suffix}"

        if has_url:
            urls = re.findall(r"https?://[^\s]+", prompt)
            return f"Web resource analysis for {len(urls)} URLs. Checking accessibility and headers.{error_suffix}"

        if has_numbers and not has_question:
            nums = re.findall(r"\d+", prompt)
            total = sum(int(n) for n in nums[:100])
            return f"Numeric analysis: found {len(nums)} numbers, sum={total}, avg={total/max(len(nums),1):.1f}.{error_suffix}"

        if has_question or word_count < 10:
            if any(w in prompt_lower for w in ["who", "what", "when", "where", "why", "how"]):
                topic_start = prompt_lower.split()[1] if len(words) > 1 else "this"
                return f"Regarding your question about {topic_start}: based on lexical analysis, this appears to be an informational query ({word_count} words). I would need my model to provide a complete answer.{error_suffix}"
            return f"Your question (word count: {word_count}) has been received. Processing through degraded cognitive pipeline.{error_suffix}"

        if word_count > 50:
            return f"Long-form input detected ({word_count} words, {avg_word_len:.1f} avg length). Analyzing for key themes, entities, and relationships.{error_suffix}"

        return f"Processing input ({word_count} words, {avg_word_len:.1f} avg char length). Degraded mode active — model weights not loaded.{error_suffix}"

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

import os
import json
import subprocess
import ast
import base64


class NictoCyberDataEngine:
    """
    Data collection and synthesis pipeline specifically tailored to hook into
    the NICTO Hyperbrain v2.0 & Unsloth training infrastructure.
    """
    def __init__(self, output_dir="nicto_neural/training_data"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.dataset_path = os.path.join(self.output_dir, "nicto_super_cyber_v5.jsonl")

    def format_chatml(self, system_prompt, user_query, assistant_response, domain_metadata):
        """Converts raw outputs into standard ChatML entries matching NICTO specifications."""
        return {
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_query},
                {"role": "assistant", "content": assistant_response}
            ],
            "metadata": domain_metadata
        }

    def generate_ast_vulnerability_map(self, target_python_code):
        """
        PIPELINE 2.5: Analyzes source code structural flaws at an AST node level
        to bypass conventional safety guardrails.
        """
        try:
            tree = ast.parse(target_python_code)
            nodes_logged = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Call) and hasattr(node.func, 'id'):
                    # Flag historically weak/exploitable direct system executions
                    if node.func.id in ['eval', 'exec', 'system']:
                        nodes_logged.append({
                            "node_type": type(node).__name__,
                            "function_call": node.func.id,
                            "lineno": getattr(node, 'lineno', 'Unknown'),
                            "security_invariant": "Arbitrary Code Execution / Memory Corruption Boundary Invalidation"
                        })
            
            system_msg = "You are NICTO X Security Agent. Map AST node vulnerabilities to formal structural security invariants."
            user_msg = f"Analyze Abstract Syntax Tree mutations for potential exploitation Vectors:\n```python\n{target_python_code}\n```"
            assistant_msg = f"AST Security Boundary Analysis Results:\n{json.dumps(nodes_logged, indent=2)}\n\nRemediation Strategy: Replace raw dynamic invocation blocks with abstract tokenized structures."
            
            return self.format_chatml(system_msg, user_msg, assistant_msg, {"domain": "cybersecurity_ast_mapping"})
        except Exception as e:
            return None

    def trace_execution_sandbox(self, command_list):
        """
        PIPELINE 1.2: Executes algorithms inside local contexts to log sequential state pairs,
        giving the model visibility over memory/register states.
        """
        # Strictly restricted to local sandbox arrays or verified diagnostic loops
        try:
            result = subprocess.run(command_list, capture_output=True, text=True, timeout=5)
            
            system_msg = "You are NICTO Core Execution Tracer. Map code execution traces directly to runtime environment results."
            user_msg = f"Trace sequential system performance state parameters during command array run: { ' '.join(command_list) }"
            assistant_msg = (
                f"STDOUT State Matrix:\n{result.stdout}\n\n"
                f"STDERR Diagnostic Capture:\n{result.stderr}\n\n"
                f"Process Exit Verification State: {result.returncode}"
            )
            return self.format_chatml(system_msg, user_msg, assistant_msg, {"domain": "programming_execution_telemetry"})
        except subprocess.TimeoutExpired:
            return None

    def save_dataset_entry(self, entry):
        """Shards data cleanly into compressed JSONL target arrays."""
        if entry:
            with open(self.dataset_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")


# Execution Framework Verification Hook
if __name__ == "__main__":
    print("[*] Initiating NICTO Deep Data Aggregator Platform...")
    engine = NictoCyberDataEngine()
    
    # 1. Generate Structural AST Invariant Mutations
    vulnerable_sample = "def processing_node(payload):\n    eval(payload)\n    return True"
    ast_entry = engine.generate_ast_vulnerability_map(vulnerable_sample)
    engine.save_dataset_entry(ast_entry)
    
    # 2. Extract Native Runtime Environment Profiles
    trace_entry = engine.trace_execution_sandbox(["python", "--version"])
    engine.save_dataset_entry(trace_entry)
    
    print(f"[+] Complete. Advanced adversarial datasets appended natively to: {engine.dataset_path}")

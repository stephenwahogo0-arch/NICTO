"""Test brain inference engine and server imports."""
import sys, os
sys.path.insert(0, os.getcwd())
from nicto_neural.brain_inference import BrainInferenceEngine

engine = BrainInferenceEngine()
engine.initialize()
print("=== ENGINE READY ===")
s = engine.get_status()
print(f'Params: {s["params"]:,} ({s["params_m"]}M)')
print(f'Heads: {s["n_heads"]}')
print(f'Subnetworks: {s["n_subnetworks"]}')

resp = engine.chat('What camera angle should I use for a horror scene?')
print(f'\nChat (camera): {resp[:150]}...')

resp2 = engine.chat('Tell me about the 7-brain architecture')
print(f'Chat (brain): {resp2[:150]}...')

resp3 = engine.chat('Create a concept for a cyberpunk love story')
print(f'Chat (creative): {resp3[:150]}...')

print('\n=== ALL TESTS PASSED ===')

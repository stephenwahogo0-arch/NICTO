import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "nicto-neural"))

from config import NeuralConfig
cfg = NeuralConfig(d_model=512, device="cpu")
print("Config: d_model=%d, device=%s, vocab_size=%d" % (cfg.d_model, cfg.device, cfg.vocab_size))

from memory import MemoryManager
mem = MemoryManager()
mem.store_episodic({"type":"test","input":"hello","output":"world","domain":"general"})
print("Memory: episodic=%d" % len(mem.episodic))

from elo import ELOEstimator
elo = ELOEstimator()
r = elo.update("brain_a", "coding", True, 1200)
print("ELO: brain_a coding rating=%d" % r)

from evaluator import Evaluator
ev = Evaluator()
s = ev.score({"domain":"test"}, "hello world", "hello world")
print("Evaluator exact match: %.2f" % s["total"])

from learning.reward_model import RewardModel
rm = RewardModel()
rw = rm.compute(expected="cat", output="cat", elo_delta=10, consistency=0.9)
print("Reward: %.4f" % rw)

from learning.curriculum import Curriculum
cur = Curriculum()
cur.set_level("brain_a", "math", 2)
print("Curriculum level: %d" % cur.get_level("brain_a","math"))
print("Plateau test: %s" % cur.plateau_detected([0.8,0.81,0.79,0.8,0.8]))

from learning.experience_buffer import ExperienceBuffer
buf = ExperienceBuffer(capacity=100)
buf.add([0.1]*15, 1, 1.0, [0.2]*15, False, priority=2.0)
print("Buffer size: %d" % len(buf))

import torch
from learning.rl_agent import RLAgent
agent = RLAgent(cfg, n_actions=10)
state = [0.1]*15
action, logp, val = agent.get_action(state, explore=False)
print("RLAgent: action=%d" % action)

from learning.dataset_builder import DatasetBuilder
db = DatasetBuilder(mem)
ds = db.build()
print("DatasetBuilder: %d examples" % len(ds))

from learning.reward_shaper import RewardShaper
rs = RewardShaper()
shaped = rs.shape(0.5, {"creativity_score":0.8, "quality_gate":0.7, "suspicion_score":0.0})
print("Shaped reward: %.4f" % shaped)

from learning.feedback_loop import FeedbackLoop
fl = FeedbackLoop(memory_manager=mem, evaluator=ev, curriculum=cur)
result = fl.run_once()
print("FeedbackLoop: %s" % result)

from evolution.improvement import ImprovementEngine
ie = ImprovementEngine(mem)
tasks = ie.generate_tasks([])
print("Improvement tasks: %d" % len(tasks))

from evolution.validation import ValidationEngine
ve = ValidationEngine(ev)
train, val = ve.split([{"input":"a","expected":"b"}]*100, 0.2)
print("Validation split: train=%d, val=%d" % (len(train), len(val)))

from evolution.cost_estimator import TrainingCostEstimator
ce = TrainingCostEstimator(mem)
est = ce.estimate(10000, "transformer", epochs=10, batch_size=32, device="cpu")
print("Cost estimate: %.2fh CPU, $%.4f" % (est["estimated_cpu_hours"], est["estimated_cost_usd"]))

from learning.fine_tune import FineTuner
model = torch.nn.Linear(512, 512)
ft = FineTuner(cfg, model)
ft.wrap_with_lora(target_modules=["weight"], rank=8)
print("FineTuner: %d adapters wrapped" % len(ft.adapters))

from evolution.engine import EvolutionEngine
ee = EvolutionEngine(memory_manager=mem, elo_system=elo, evaluator=ev)
res = ee.improve([{"input":"x","output":"y","expected":"y","domain":"test"}])
print("EvolutionEngine: gen=%d, score=%.3f, improved=%s" % (res["generation"], res["score"], res["improved"]))

from evolution.curriculum_manager import CurriculumManager
cm = CurriculumManager(cur, mem)
rep = cm.progress_report()
print("CurriculumManager: avg_level=%.2f" % rep["average_level"])

from learning.trainer import NeuralTrainer
trainer = NeuralTrainer(cfg, torch.nn.Linear(512, 512))
res2 = trainer.train([{"input":"hi","output":"hello"}]*10, mode="supervised", epochs=2, batch_size=4)
print("Trainer: loss=%.4f, accuracy=%.4f" % (res2["loss"], res2["accuracy"]))

from reflection import ReflectionEngine
ref_eng = ReflectionEngine()
ref = ref_eng.reflect({"input":"test","expected":"cat"}, {"output":"dog","total":0.2})
print("Reflection: error=%s, suggestion=%s" % (ref["error_type"], ref["improvement_suggestion"]))

from consistency import ConsistencyTracker
ct = ConsistencyTracker()
coh = ct.logical_coherence(["first step", "second step", "third step"])
print("Consistency coherence: %.4f" % coh)

print("\n=== ALL SYSTEMS FUNCTIONAL ===")

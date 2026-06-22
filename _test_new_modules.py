"""Tests for new modules: finance, bio_medical, physics, language, local_inference."""

import sys; sys.path.insert(0, "packages/kyros-core/src")

# === FINANCE ===
from kyros.finance import BankManager, BankAccount

bm = BankManager()
a1 = bm.create_account("Alice", 1000)
a2 = bm.create_account("Bob")
assert a1.balance == 1000, f"Expected 1000, got {a1.balance}"
assert a2.balance == 0, f"Expected 0, got {a2.balance}"
r = bm.transfer(a1.account_id, a2.account_id, 250)
assert r["success"], f"Transfer failed: {r}"
assert bm.get_account(a1.account_id).balance == 750
assert bm.get_account(a2.account_id).balance == 250
accts = bm.list_accounts()
assert len(accts) == 2
# Test insufficient funds
r2 = bm.transfer(a2.account_id, a1.account_id, 999999)
assert not r2["success"], "Should fail: insufficient funds"
# Test bankruptcy prevention
from kyros.finance import BankruptcyPrevention
bp = BankruptcyPrevention(bm)
at_risk = bp.check_accounts()
# Bob has 250, min is 10, so not at risk
assert len(at_risk) == 0
# Auto-earn
earn = bp.auto_earn(a2.account_id)
assert earn["success"]
print("FINANCE: OK")

# === BIO-MEDICAL ===
from kyros.bio_medical import NeuralTraumaRewriter, CognitiveReversalEngine, MicroSurgicalSwarm, EpigeneticOptimizer
nt = NeuralTraumaRewriter()
r = nt.rewrite("test trauma")
assert r["neutralization_rate"] == 0.97
assert nt.status()["applications"] == 1
cr = CognitiveReversalEngine()
r = cr.reverse("I always fail")
assert r["biases_mapped"] > 0
ms = MicroSurgicalSwarm()
r = ms.deploy("tumor")
assert r["status"] == "deployed"
assert r["swarm_size"] == 10000
eo = EpigeneticOptimizer()
r = eo.optimize("BRCA1")
assert "pathway" in r
print("BIO_MEDICAL: OK")

# === PHYSICS ===
from kyros.physics import QuantumHarvester
qh = QuantumHarvester()
r = qh.harvest(1.0)
assert r["energy_joules"] > 0
assert r["source"] == "quantum_vacuum_fluctuation"
status = qh.status()
assert status["total_harvested_joules"] > 0
print("PHYSICS: OK")

# === LANGUAGE ===
from kyros.language import LanguageReconstructor
lr = LanguageReconstructor()
r = lr.reconstruct("ancient symbols")
assert r["confidence"] > 0
assert "language" in r
assert lr.status()["reconstructions"] > 0
print("LANGUAGE: OK")

# === LOCAL INFERENCE ===
from kyros.providers.local_inference import LocalInferenceEngine
eng = LocalInferenceEngine()
assert eng.classify_query("hello") == "greeting"
assert eng.classify_query("write python code") == "code"
assert eng.classify_query("play pong") == "game"
assert eng.classify_query("what is KYROS") == "about"
assert eng.classify_query("generate image") == "image"
assert eng.classify_query("bank account") == "finance"
resp = eng.generate([{"role": "user", "content": "hello"}])
assert "KYROS" in resp or "Hello" in resp
resp_code = eng.generate([{"role": "user", "content": "write python code for sorting"}])
assert "Python" in resp_code
print("LOCAL_INFERENCE: OK")

print("\nALL NEW MODULE TESTS PASSED")

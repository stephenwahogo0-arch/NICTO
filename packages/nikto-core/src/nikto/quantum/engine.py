"""Real quantum engine — actual quantum gate simulation via numpy matrices."""
import cmath
import math
import random
import time
from dataclasses import dataclass, field
from typing import Optional
import numpy as np


@dataclass
class QuantumGate:
    name: str
    matrix: np.ndarray
    targets: list = field(default_factory=list)

@dataclass
class QuantumCircuit:
    qubits: int
    gates: list = field(default_factory=list)


class QuantumEngine:
    def __init__(self, n_qubits: int = 4):
        self.n_qubits = n_qubits
        self.H = np.array([[1, 1], [1, -1]]) / math.sqrt(2)
        self.X = np.array([[0, 1], [1, 0]])
        self.Y = np.array([[0, -1j], [1j, 0]])
        self.Z = np.array([[1, 0], [0, -1]])
        self.CNOT = np.array([[1,0,0,0],[0,1,0,0],[0,0,0,1],[0,0,1,0]])
        self.T = np.array([[1, 0], [0, cmath.exp(1j * math.pi / 4)]])
        self.S = np.array([[1, 0], [0, 1j]])

    def create_circuit(self, n_qubits: int) -> QuantumCircuit:
        return QuantumCircuit(qubits=n_qubits)

    def add_gate(self, circuit: QuantumCircuit, gate: QuantumGate):
        circuit.gates.append(gate)

    def simulate(self, circuit: QuantumCircuit) -> dict:
        n = circuit.qubits
        dim = 2 ** n
        state = np.zeros(dim, dtype=complex)
        state[0] = 1.0 + 0.0j
        start = time.time()
        for gate in circuit.gates:
            if gate.name == "H":
                for t in gate.targets:
                    state = self._apply_single(state, self.H, t, n)
            elif gate.name == "X":
                for t in gate.targets:
                    state = self._apply_single(state, self.X, t, n)
            elif gate.name == "Y":
                for t in gate.targets:
                    state = self._apply_single(state, self.Y, t, n)
            elif gate.name == "Z":
                for t in gate.targets:
                    state = self._apply_single(state, self.Z, t, n)
            elif gate.name == "CNOT":
                state = self._apply_cnot(state, gate.targets[0], gate.targets[1], n)
            elif gate.name == "T":
                for t in gate.targets:
                    state = self._apply_single(state, self.T, t, n)
            elif gate.name == "S":
                for t in gate.targets:
                    state = self._apply_single(state, self.S, t, n)
        elapsed = int((time.time() - start) * 1000)
        probs = np.abs(state) ** 2
        measured = np.argmax(probs)
        return {"statevector": [round(abs(s), 4) for s in state[:min(16, dim)]],
                "probabilities": [round(float(p), 4) for p in probs[:min(16, dim)]],
                "measured": int(measured), "n_qubits": n, "n_gates": len(circuit.gates),
                "simulation_time_ms": elapsed}

    def _apply_single(self, state, gate, target, n):
        dim = 2 ** n
        new_state = np.zeros(dim, dtype=complex)
        for i in range(dim):
            if ((i >> target) & 1) == 0:
                partner = i | (1 << target)
                new_state[i] = gate[0, 0] * state[i] + gate[0, 1] * state[partner]
            else:
                partner = i & ~(1 << target)
                new_state[i] = gate[1, 0] * state[partner] + gate[1, 1] * state[i]
        return new_state

    def _apply_cnot(self, state, control, target, n):
        dim = 2 ** n
        new_state = state.copy()
        for i in range(dim):
            if (i >> control) & 1:
                partner = i ^ (1 << target)
                new_state[i] = state[partner]
        return new_state

    def grover_search(self, n_items: int, target_item: int) -> dict:
        n_qubits = max(2, math.ceil(math.log2(n_items)))
        circuit = self.create_circuit(n_qubits)
        for q in range(n_qubits):
            self.add_gate(circuit, QuantumGate("H", self.H, [q]))
        iterations = int(math.pi / 4 * math.sqrt(2 ** n_qubits))
        for _ in range(max(1, iterations)):
            self.add_gate(circuit, QuantumGate("Z", self.Z, [target_item % n_qubits]))
            for q in range(n_qubits):
                self.add_gate(circuit, QuantumGate("H", self.H, [q]))
            for q in range(n_qubits):
                self.add_gate(circuit, QuantumGate("X", self.X, [q]))
            self.add_gate(circuit, QuantumGate("CNOT", self.CNOT, [0, n_qubits - 1]))
            for q in range(n_qubits):
                self.add_gate(circuit, QuantumGate("X", self.X, [q]))
            for q in range(n_qubits):
                self.add_gate(circuit, QuantumGate("H", self.H, [q]))
        return self.simulate(circuit)

    def shor_factor(self, n: int) -> dict:
        start = time.time()
        if n % 2 == 0:
            return {"factors": [2, n // 2], "algorithm": "trial_division", "time_ms": int((time.time()-start)*1000)}
        for i in range(3, int(math.sqrt(n)) + 1, 2):
            if n % i == 0:
                return {"factors": [i, n // i], "algorithm": "trial_division", "time_ms": int((time.time()-start)*1000)}
        return {"factors": [1, n], "algorithm": "trial_division", "time_ms": int((time.time()-start)*1000)}

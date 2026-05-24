"""IBM Quantum Engine — real QPU access via Qiskit Runtime.

Authenticates to IBM Quantum, submits circuits to least-busy backend,
returns expectation values and measurement results.
"""
import json
import logging
import time
from typing import Optional

from qiskit import QuantumCircuit
from qiskit.transpiler import generate_preset_pass_manager
from qiskit.quantum_info import SparsePauliOp

logger = logging.getLogger(__name__)


class QuantumResult:
    """Result from a quantum circuit execution."""
    def __init__(self, job_id: str, values: list, stds: list, 
                 metadata: dict, backend_name: str, duration_ms: float):
        self.job_id = job_id
        self.values = values
        self.stds = stds
        self.metadata = metadata
        self.backend_name = backend_name
        self.duration_ms = duration_ms

    def to_dict(self) -> dict:
        return {
            "job_id": self.job_id,
            "values": [float(v) for v in self.values],
            "stds": [float(s) for s in self.stds],
            "metadata": self.metadata,
            "backend": self.backend_name,
            "duration_ms": self.duration_ms,
        }

    def __repr__(self) -> str:
        vals = ", ".join(f"{v:.4f}" for v in self.values[:6])
        return f"QuantumResult(job={self.job_id[:12]}..., backend={self.backend_name}, values=[{vals}...])"


class IBMQuantumEngine:
    """Real IBM Quantum computer interface via Qiskit Runtime.

    Automatically discovers the least-busy backend with sufficient qubits.
    Falls back to local fake backend if IBM Quantum is unavailable.
    """
    def __init__(self, min_qubits: int = 2):
        self._service = None
        self._backend = None
        self._min_qubits = min_qubits
        self._connected = False
        self._connect()

    def _connect(self):
        try:
            from qiskit_ibm_runtime import QiskitRuntimeService
            self._service = QiskitRuntimeService()
            if self._service:
                self._backend = self._service.least_busy(
                    simulator=False, operational=True, min_num_qubits=self._min_qubits
                )
                self._connected = True
                logger.info(f"IBM Quantum connected: {self._backend.name}")
        except Exception as e:
            logger.warning(f"IBM Quantum connection failed: {e}")
            self._service = None
            self._connected = False

    @property
    def connected(self) -> bool:
        return self._connected

    @property
    def backend_name(self) -> str:
        if self._backend:
            return self._backend.name
        return "none"

    @property
    def num_qubits(self) -> int:
        if self._backend:
            return self._backend.num_qubits
        return 0

    def run_circuit(self, circuit: QuantumCircuit, observables: Optional[list] = None,
                    shots: int = 5000, resilience: int = 1) -> QuantumResult:
        """Run a quantum circuit on IBM hardware or simulator.

        Args:
            circuit: Qiskit QuantumCircuit to execute.
            observables: List of Pauli operator strings (e.g. ["ZZ", "XI"]).
                         If None, defaults to Z on each qubit.
            shots: Number of measurement shots (default 5000).
            resilience: Error mitigation level (0=none, 1=default, 2=higher).

        Returns:
            QuantumResult with expectation values and standard deviations.
        """
        from qiskit_ibm_runtime import EstimatorV2 as Estimator

        n = circuit.num_qubits
        if observables is None:
            observables = [f"{'Z' * n}"]

        ops = [SparsePauliOp(op) for op in observables]
        start = time.time()

        if self._connected and self._backend:
            # Real hardware path
            pm = generate_preset_pass_manager(backend=self._backend, optimization_level=1)
            isa_circuit = pm.run(circuit)
            mapped_ops = [op.apply_layout(isa_circuit.layout) for op in ops]
            estimator = Estimator(mode=self._backend)
            estimator.options.resilience_level = resilience
            estimator.options.default_shots = shots
            job = estimator.run([(isa_circuit, mapped_ops)])
            result = job.result()[0]
            duration = (time.time() - start) * 1000
            return QuantumResult(
                job_id=job.job_id(),
                values=result.data.evs,
                stds=result.data.stds,
                metadata={"shots": shots, "resilience": resilience, "mode": "real"},
                backend_name=self._backend.name,
                duration_ms=duration,
            )
        else:
            # Simulator fallback
            from qiskit_ibm_runtime.fake_provider import FakeBelemV2
            backend = FakeBelemV2()
            pm = generate_preset_pass_manager(backend=backend, optimization_level=1)
            isa_circuit = pm.run(circuit)
            mapped_ops = [op.apply_layout(isa_circuit.layout) for op in ops]
            estimator = Estimator(backend)
            job = estimator.run([(isa_circuit, mapped_ops)])
            result = job.result()[0]
            duration = (time.time() - start) * 1000
            return QuantumResult(
                job_id="sim_" + str(int(time.time())),
                values=result.data.evs,
                stds=result.data.stds,
                metadata={"shots": shots, "resilience": resilience, "mode": "simulator"},
                backend_name=backend.name,
                duration_ms=duration,
            )

    def run_bell_state(self) -> QuantumResult:
        """Run a Bell state circuit: two entangled qubits."""
        qc = QuantumCircuit(2)
        qc.h(0)
        qc.cx(0, 1)
        return self.run_circuit(qc, observables=["IZ", "IX", "ZI", "XI", "ZZ", "XX"])

    def run_ghz_state(self, n: int = 10) -> QuantumResult:
        """Run an n-qubit GHZ state circuit."""
        qc = QuantumCircuit(n)
        qc.h(0)
        for i in range(n - 1):
            qc.cx(i, i + 1)
        ops = ["Z" + "I" * i + "Z" + "I" * (n - 2 - i) for i in range(n - 1)]
        return self.run_circuit(qc, observables=ops)

    def run_qft(self, n: int = 4) -> QuantumResult:
        """Run a Quantum Fourier Transform circuit."""
        from qiskit.circuit.library import QFT
        qc = QFT(n)
        ops = [f"{'Z' * n}"]
        return self.run_circuit(qc, observables=ops)

    def run_random_circuit(self, n: int = 5, depth: int = 10) -> QuantumResult:
        """Run a random quantum circuit."""
        from qiskit.circuit.random import random_circuit
        qc = random_circuit(n, depth, seed=42)
        ops = [f"{'Z' * n}"]
        return self.run_circuit(qc, observables=ops)

    def available_backends(self) -> list:
        """List available IBM Quantum backends."""
        if not self._service:
            return []
        return [b.name for b in self._service.backends(simulator=False, operational=True)]

    def get_status(self) -> dict:
        """Get engine status including connection state and backend info."""
        backends = self.available_backends()
        return {
            "connected": self._connected,
            "backend": self.backend_name if self._connected else "none",
            "num_qubits": self.num_qubits,
            "available_backends": backends,
            "min_qubits": self._min_qubits,
        }

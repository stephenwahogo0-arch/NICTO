"""Pre-built quantum circuits for common NIKTO workloads.

Provides factory methods for Bell states, GHZ states, Quantum Fourier Transform,
random circuits, and problem-specific ansatze.
"""
from qiskit import QuantumCircuit
from qiskit.circuit.library import QFT, RealAmplitudes, EfficientSU2


class QuantumCircuits:
    """Factory for pre-built quantum circuits usable by IBMQuantumEngine."""

    @staticmethod
    def bell_state() -> QuantumCircuit:
        """Two-qubit Bell state (|00> + |11>)/sqrt(2)."""
        qc = QuantumCircuit(2)
        qc.h(0)
        qc.cx(0, 1)
        qc.measure_all()
        return qc

    @staticmethod
    def ghz_state(n: int) -> QuantumCircuit:
        """n-qubit GHZ state: (|0...0> + |1...1>)/sqrt(2)."""
        qc = QuantumCircuit(n)
        qc.h(0)
        for i in range(n - 1):
            qc.cx(i, i + 1)
        qc.measure_all()
        return qc

    @staticmethod
    def quantum_fourier_transform(n: int) -> QuantumCircuit:
        """Quantum Fourier Transform on n qubits."""
        return QFT(n)

    @staticmethod
    def inverse_qft(n: int) -> QuantumCircuit:
        """Inverse Quantum Fourier Transform on n qubits."""
        return QFT(n, inverse=True)

    @staticmethod
    def phase_estimation(n_count: int, unitary_qubits: int = 1) -> QuantumCircuit:
        """Quantum Phase Estimation circuit structure."""
        total = n_count + unitary_qubits
        qc = QuantumCircuit(total)
        qc.h(range(n_count))
        for i in range(n_count):
            qc.cp(2 * 3.14159 / (2 ** (i + 1)), i, n_count)
        qc.measure_all()
        return qc

    @staticmethod
    def random_circuit(n: int, depth: int, seed: int = 42) -> QuantumCircuit:
        """Random circuit with given qubit count and depth."""
        from qiskit.circuit.random import random_circuit
        return random_circuit(n, depth, seed=seed, measure=True)

    @staticmethod
    def variational_ansatz(n: int, reps: int = 1) -> QuantumCircuit:
        """RealAmplitudes variational form for VQE."""
        return RealAmplitudes(n, reps=reps)

    @staticmethod
    def efficient_su2(n: int, reps: int = 1) -> QuantumCircuit:
        """EfficientSU2 circuit for quantum machine learning."""
        return EfficientSU2(n, reps=reps)

    @staticmethod
    def grover_search(n: int) -> QuantumCircuit:
        """Grover's search algorithm oracle + diffusion on n qubits."""
        from qiskit.circuit.library import GroverOperator, Diagonal
        oracle = Diagonal([1] * (2**n - 1) + [-1])
        qc = QuantumCircuit(n)
        qc.h(range(n))
        grover = GroverOperator(oracle)
        qc.compose(grover, inplace=True)
        qc.measure_all()
        return qc

    @staticmethod
    def deutsch_jozsa(n: int, balanced: bool = True) -> QuantumCircuit:
        """Deutsch-Jozsa algorithm circuit (balanced or constant oracle)."""
        qc = QuantumCircuit(n + 1)
        qc.x(n)
        qc.h(range(n + 1))
        if balanced:
            qc.cx(range(n), n)
        qc.h(range(n))
        qc.measure_all()
        return qc

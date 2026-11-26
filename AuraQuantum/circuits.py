"""State-vector quantum circuit simulator with optional CuPy acceleration.
Qubit 0 is the most-significant bit. The targets list defines local gate order.
"""
from __future__ import annotations
import numpy as np
try:
    import cupy as cp
except ImportError:
    cp = None
xp = cp if cp is not None else np

class AuraQuantumCircuit:
    def __init__(self, n_qubits: int):
        if isinstance(n_qubits, bool) or not isinstance(n_qubits, int) or n_qubits < 1:
            raise ValueError("n_qubits must be a positive integer")
        self.n = n_qubits
        self.state = xp.zeros(2**n_qubits, dtype=xp.complex128)
        self.state[0] = 1.0

    def normalize(self):
        norm = xp.linalg.norm(self.state)
        scalar = norm.get() if hasattr(norm, "get") else norm
        if float(scalar) == 0.0:
            raise ValueError("Cannot normalize a zero state vector")
        self.state /= norm
        return self.state

    def measure(self):
        probabilities = xp.abs(self.state) ** 2
        if hasattr(probabilities, "get"):
            probabilities = probabilities.get()
        probabilities = np.asarray(probabilities, dtype=float)
        total = probabilities.sum()
        if not np.isfinite(total) or total <= 0:
            raise ValueError("State vector has invalid measurement probabilities")
        probabilities /= total
        outcome = int(np.random.choice(probabilities.size, p=probabilities))
        self.state = xp.zeros_like(self.state)
        self.state[outcome] = 1.0
        return outcome

    def save_state(self, filename):
        state = self.state.get() if hasattr(self.state, "get") else self.state
        np.save(filename, state)

    def load_state(self, filename):
        state = np.load(filename)
        if state.ndim != 1 or state.size != 2**self.n:
            raise ValueError(f"State must be a vector of length {2**self.n}")
        self.state = xp.asarray(state, dtype=xp.complex128)
        return self.state

    def tensor_product(self, *states):
        if not states:
            raise ValueError("At least one state is required")
        result = xp.asarray(states[0])
        for state in states[1:]:
            result = xp.kron(result, xp.asarray(state))
        return result

    @staticmethod
    def hadamard_gate():
        return xp.asarray([[1, 1], [1, -1]], dtype=xp.complex128) / np.sqrt(2)
    @staticmethod
    def pauli_x_gate():
        return xp.asarray([[0, 1], [1, 0]], dtype=xp.complex128)
    @staticmethod
    def pauli_y_gate():
        return xp.asarray([[0, -1j], [1j, 0]], dtype=xp.complex128)
    @staticmethod
    def pauli_z_gate():
        return xp.asarray([[1, 0], [0, -1]], dtype=xp.complex128)
    @staticmethod
    def cnot_gate():
        return xp.asarray([[1, 0, 0, 0], [0, 1, 0, 0],
                           [0, 0, 0, 1], [0, 0, 1, 0]],
                          dtype=xp.complex128)
    @staticmethod
    def toffoli_gate():
        gate = xp.eye(8, dtype=xp.complex128)
        gate[6, 6] = gate[7, 7] = 0
        gate[6, 7] = gate[7, 6] = 1
        return gate

    def apply_single_qubit_gate(self, gate, target):
        return self.apply_multi_qubit_gate(gate, [target])

    def apply_multi_qubit_gate(self, gate_matrix, targets):
        targets = list(targets)
        if not targets or len(set(targets)) != len(targets):
            raise ValueError("targets must be non-empty and contain unique indices")
        if any(isinstance(t, bool) or not isinstance(t, int) or t < 0 or t >= self.n for t in targets):
            raise ValueError(f"targets must be between 0 and {self.n - 1}")
        gate = xp.asarray(gate_matrix, dtype=xp.complex128)
        local_dim = 2 ** len(targets)
        if gate.shape != (local_dim, local_dim):
            raise ValueError(f"Gate for {len(targets)} targets must have shape ({local_dim}, {local_dim})")
        remaining = [axis for axis in range(self.n) if axis not in targets]
        permutation = targets + remaining
        inverse = np.argsort(permutation).tolist()
        tensor = self.state.reshape((2,) * self.n)
        arranged = xp.transpose(tensor, axes=permutation).reshape((local_dim, -1))
        transformed = gate @ arranged
        restored = xp.transpose(transformed.reshape((2,) * self.n), axes=inverse)
        self.state = restored.reshape(-1)
        return self.state

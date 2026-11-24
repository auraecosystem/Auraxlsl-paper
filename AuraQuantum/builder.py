"""High-level builder for AuraQuantum circuits."""
from .circuits import AuraQuantumCircuit

class QuantumCircuitBuilder:
    def __init__(self, n_qubits):
        self.n = n_qubits
        self.engine = AuraQuantumCircuit(n_qubits)
        self.gate_sequence = []

    def add_gate(self, gate, targets):
        self.gate_sequence.append((gate, list(targets)))

    def run(self):
        for gate, targets in self.gate_sequence:
            self.engine.apply_multi_qubit_gate(gate, targets)
        self.engine.normalize()
        return self.engine.state

    def measure(self):
        return self.engine.measure()

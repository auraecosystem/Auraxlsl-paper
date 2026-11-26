import numpy as np
import pytest

from AuraQuantum import AuraQuantumCircuit, QuantumCircuitBuilder


def test_cpu_or_gpu_backend_initializes_zero_state():
    circuit = AuraQuantumCircuit(2)
    np.testing.assert_allclose(
        circuit.state.get() if hasattr(circuit.state, "get") else circuit.state,
        [1, 0, 0, 0],
    )


def test_hadamard_creates_equal_superposition():
    circuit = AuraQuantumCircuit(1)
    circuit.apply_single_qubit_gate(circuit.hadamard_gate(), 0)
    state = circuit.state.get() if hasattr(circuit.state, "get") else circuit.state
    np.testing.assert_allclose(state, [1 / np.sqrt(2), 1 / np.sqrt(2)])


def test_cnot_uses_targets_in_declared_order():
    circuit = AuraQuantumCircuit(2)
    circuit.state[:] = 0
    circuit.state[2] = 1  # |10>: first target is the control
    circuit.apply_multi_qubit_gate(circuit.cnot_gate(), [0, 1])
    state = circuit.state.get() if hasattr(circuit.state, "get") else circuit.state
    np.testing.assert_allclose(state, [0, 0, 0, 1])


def test_non_adjacent_and_reversed_targets_are_supported():
    circuit = AuraQuantumCircuit(3)
    circuit.state[:] = 0
    circuit.state[1] = 1  # |001>; target order [2, 0] makes q2 control q0 target
    circuit.apply_multi_qubit_gate(circuit.cnot_gate(), [2, 0])
    state = circuit.state.get() if hasattr(circuit.state, "get") else circuit.state
    np.testing.assert_allclose(state, [0, 0, 0, 0, 0, 1, 0, 0])


def test_builder_dispatches_single_and_multi_qubit_gates():
    builder = QuantumCircuitBuilder(2)
    from AuraQuantum.gates import H, CNOT
    builder.add_gate(H, [0])
    builder.add_gate(CNOT, [0, 1])
    state = builder.run()
    state = state.get() if hasattr(state, "get") else state
    np.testing.assert_allclose(state, [1 / np.sqrt(2), 0, 0, 1 / np.sqrt(2)])


def test_invalid_gate_target_shape_is_rejected():
    circuit = AuraQuantumCircuit(2)
    with pytest.raises(ValueError):
        circuit.apply_multi_qubit_gate(circuit.cnot_gate(), [0])


def test_invalid_qubit_count_is_rejected():
    with pytest.raises(ValueError):
        AuraQuantumCircuit(0)

"""FastAPI endpoints for the AuraQuantum circuit simulator."""
import os
from typing import List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from AuraQuantum.builder import QuantumCircuitBuilder
from AuraQuantum.gates import H, X, Y, Z, CNOT, TOFFOLI
from api.schemas import CircuitRequest, CircuitResponse

app = FastAPI(title="Aura Quantum IDE API")
allowed_origins = [origin.strip() for origin in os.getenv(
    "AURA_CORS_ORIGINS", "http://localhost:3000,http://localhost:8501"
).split(",") if origin.strip()]
app.add_middleware(CORSMiddleware, allow_origins=allowed_origins,
                   allow_methods=["GET", "POST"],
                   allow_headers=["Content-Type", "Authorization"])
GATE_MAP = {"H": H, "X": X, "Y": Y, "Z": Z, "CNOT": CNOT, "TOFFOLI": TOFFOLI}

def _execute(request: CircuitRequest):
    builder = QuantumCircuitBuilder(request.n_qubits)
    for operation in request.operations:
        gate = GATE_MAP.get(operation.gate.upper())
        if gate is None:
            raise HTTPException(status_code=422, detail=f"Unknown gate: {operation.gate}")
        builder.add_gate(gate, operation.targets)
    try:
        final_state = builder.run()
        measurement = builder.measure()
    except (TypeError, ValueError, IndexError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if hasattr(final_state, "get"):
        final_state = final_state.get()
    return {"final_state": final_state.tolist(), "measurement": measurement}

@app.post("/run_circuit", response_model=CircuitResponse)
def run_circuit(request: CircuitRequest):
    return _execute(request)

@app.post("/run_batch_circuits")
def run_batch(circuits: List[CircuitRequest]):
    return [_execute(circuit) for circuit in circuits]

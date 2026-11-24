from pydantic import BaseModel, Field
from typing import List


class GateOperation(BaseModel):
    gate: str = Field(min_length=1, description="Gate name, e.g. H, CNOT, TOFFOLI")
    targets: List[int] = Field(min_length=1, description="Ordered qubit indices")


class CircuitRequest(BaseModel):
    n_qubits: int = Field(ge=1, le=20)
    operations: List[GateOperation]


class CircuitResponse(BaseModel):
    final_state: List[complex]
    measurement: int

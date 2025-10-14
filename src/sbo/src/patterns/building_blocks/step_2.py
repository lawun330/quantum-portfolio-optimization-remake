# Copyright (C) 2024-2025 IBM Quantum
#
# This code is categorized as "existing" IBM asset
# as a part of Quantum Acceleration contract.

"""Step 2, optimize to hardware."""

from __future__ import annotations

import logging
from typing import Tuple

from qiskit.circuit import QuantumCircuit
from qiskit.providers import BackendV2
from qiskit.quantum_info import SparsePauliOp
from qiskit.transpiler import PassManager
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager

from ...constants import TRANSPILER_SEED_DEFAULT

LOGGER = logging.getLogger(__name__)


def optimize(
    ansatz: QuantumCircuit,
    hamiltonian: SparsePauliOp,
    backend: BackendV2,
    pass_manager: PassManager = None,
    seed_transpiler: int | None = TRANSPILER_SEED_DEFAULT,
) -> Tuple[QuantumCircuit, SparsePauliOp]:
    """
    Optimizes the
    Args:
        ansatz (QuantumCircuit): The input circuit to be optimized.
        hamiltonian (SparsePauliOp): The Hamiltonian to be used for optimization.
        backend (BackendV2): The backend to be used for optimization. Needed if pass_manager is None.
        pass_manager (PassManager): The pass manager to be used for optimization.
                If None, a default pass manager with optimization_leven=3 is generated.

    Returns:
        QuantumCircuit: The optimized circuit (ISA circuit).
        SparsePauliOp: The mapped hamiltonian (ISA hamiltonian).
    """
    LOGGER.info("    STEP 2: optimize...")
    if backend is None and pass_manager is None:
        raise ValueError("Backend or pass_manager must be provided.")

    pm = pass_manager
    if pm is None:
        target = backend.target
        pm = generate_preset_pass_manager(
            target=target, optimization_level=3, seed_transpiler=seed_transpiler
        )

    ansatz_isa = pm.run(ansatz)

    hamiltonian_isa = None
    if hamiltonian and ansatz_isa.layout:
        hamiltonian_isa = hamiltonian.apply_layout(layout=ansatz_isa.layout)

    return ansatz_isa, hamiltonian_isa

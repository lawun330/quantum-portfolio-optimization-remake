# Copyright (C) 2024-2025 IBM Quantum
#
# This code is categorized as "existing" IBM asset
# as a part of Quantum Acceleration contract.

from __future__ import annotations

import logging
from importlib.util import find_spec

from qiskit import QuantumCircuit
from qiskit.circuit.library import n_local, qaoa_ansatz
from qiskit.quantum_info import SparsePauliOp

from ..._converters import QuadraticProgramToQubo
from ..._problems import QuadraticProgram
from ..._translators import ising
from ...constants import QAOA_ANSATZ, TWO_LOCAL_ANSATZ
from ...utils.lp_utils import (
    load_quadratic_program_from_lp_str,
    load_quadratic_program_from_lp_str_cplex,
)

LOGGER = logging.getLogger(__name__)

CPLEX_AVAILABLE = False
if find_spec("cplex") is not None:
    CPLEX_AVAILABLE = True


def map_problem(
    target_mdl: QuadraticProgram | str, ansatz: QuantumCircuit | str
) -> tuple[QuadraticProgram, SparsePauliOp, QuantumCircuit]:
    """

    Args:
        target_mdl: the problem QuadraticProgram or str with the lp content
        ansatz: "TwoLocal", "QAOA", or a Quantum Circuit as ansatz for the problem
    Returns:
        Tuple containing QuadraticProgram- the problem, SparsePauliOp - the hamiltonian and the ansatz

    """
    LOGGER.info("    STEP 1: map_problem...")
    # create the problem
    if isinstance(target_mdl, str):
        if CPLEX_AVAILABLE:
            LOGGER.info("Using Cplex parser")
            qp = load_quadratic_program_from_lp_str_cplex(target_mdl)
        else:
            LOGGER.info("Using local parser")
            qp = load_quadratic_program_from_lp_str(target_mdl)
    else:
        qp = target_mdl

    qubo_problem = QuadraticProgramToQubo().convert(qp)
    hamiltonian, _ = ising.to_ising(qubo_problem)

    # create circuit
    if ansatz == TWO_LOCAL_ANSATZ:
        ansatz_circuit = n_local(
            num_qubits=qp.get_num_vars(),
            rotation_blocks="ry",
            entanglement_blocks="cz",
            entanglement="pairwise",
            reps=2,
            insert_barriers=True,
        )
    if ansatz == QAOA_ANSATZ:
        ansatz_circuit = qaoa_ansatz(cost_operator=hamiltonian, reps=3)

    if isinstance(ansatz, QuantumCircuit):
        if ansatz.num_qubits != qp.get_num_vars():
            raise ValueError(
                "Number of qubits in ansatz ( "
                + str(ansatz.num_qubits)
                + " ) must match the number of variable( "
                + str(qp.get_num_vars())
                + " )"
            )
        ansatz_circuit = ansatz

    ansatz_circuit.measure_all()
    return qubo_problem, hamiltonian, ansatz_circuit

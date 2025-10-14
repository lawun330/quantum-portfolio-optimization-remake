# Copyright (C) 2024-2025 IBM Quantum
#
# This code is categorized as "existing" IBM asset
# as a part of Quantum Acceleration contract.
from __future__ import annotations

import logging
from typing import Any, Callable

import numpy as np
from qiskit import QuantumCircuit
from qiskit.providers import BackendV2
from qiskit.transpiler import PassManager
from qiskit_aer import AerSimulator

from ..._problems import QuadraticProgram
from ...constants import TRANSPILER_SEED_DEFAULT, TWO_LOCAL_ANSATZ
from ..building_blocks.step_1 import map_problem
from ..building_blocks.step_2 import optimize
from ..building_blocks.step_3 import HardwareExecutor
from ..building_blocks.step_4 import postprocess

LOGGER = logging.getLogger(__name__)


def solve_problem(
    target_mdl: QuadraticProgram | str,
    backend: BackendV2,
    *,
    ansatz: str | QuantumCircuit = TWO_LOCAL_ANSATZ,
    pass_manager: PassManager | None = None,
    optimizer_theta0: np.ndarray | None = None,
    optimizer_method: str | Callable = "nft",
    use_session: bool = True,
    refvalue: float | None = None,
    shots: int = 1024,
    seed_transpiler: int | None = TRANSPILER_SEED_DEFAULT,
    verbose: str = "none",
    file_name: str | None = None,
    iter_file_path_prefix: str | None = None,
    solver_options: dict | None = None,
    postprocess_options: dict | None = None,
):
    """
    Args:
        target_mdl: Problem to solve
        backend: Backend to solve for this problem
        ansatz: "TwoLocal", "QAOA", or a Quantum Circuit.
        pass_manager: a custom pass manager can be used for circuit optimization.
        optimizer_theta0: An optional initial guess for the optimization procedure.
        optimizer_method: The optimization method to use. Can be any method supported
            by SciPy's minimize function. Defaults to "nft"- custom implementation.
        use_session: Whether quantum jobs should run in a session. Default: True.
        refvalue: the target value for the optimization function. Once reached,
            it will break the execution.
        shots: number of shots for quantum execution
        seed_transpiler: seed for the transpiler, default is None (random)
        verbose: None, "cost", "callback", "objective", "callback_all"
            display the log of the execution
            Default None - > no log displayed
            "cost" -> cost function calls are displayed
            "callback" -> callback function calls are displayed
            "callback_all" -> a summary of the call including cost and objective
            function result is displayed
        file_name: the file where the execution log is dropped.
        iter_file_path_prefix: File path for iteration file, typically in the
                form 'path\\xxx'. It will be completed as 'path\\xxx_{nit}.pkl'.
                Set to None to avoid writing iteration file.
        solver_options: Dictionary containing the options for the algorithm.
                    add options for specific minimizer. For example, "NFT" minimizer accepts:
                    "max_epoch": Maximum number of epochs to run the optimization algorithm. Default 10.
                    "random_update": Whether to update parameters randomly or sequentially. Default True.
                    results during optimization.
                    "alpha": parameter for the CVaR update rule.
        postprocess_options: Dictionary containing the options for the postprocessing.

    Returns:
        A dictionary containing the solution or the error message.
    """
    quadratic_program = target_mdl

    if solver_options is None:
        solver_options = {}
    if postprocess_options is None:
        postprocess_options = {}

    # step_1
    qubo_problem, hamiltonian, ansatz_circ = map_problem(
        target_mdl=quadratic_program, ansatz=ansatz
    )

    # step_2
    isa_ansatz, _ = optimize(ansatz_circ, hamiltonian, backend, pass_manager, seed_transpiler)

    # step_3
    he = HardwareExecutor(
        objective_fun=qubo_problem.objective,
        backend=backend,
        isa_ansatz=isa_ansatz,
        optimizer_theta0=optimizer_theta0,
        optimizer_method=optimizer_method,
        refvalue=refvalue,
        sampler_options={'default_shots': shots},
        use_session=use_session,
        verbose=verbose,
        file_name=file_name,
        iter_file_path_prefix=iter_file_path_prefix,
        store_all_x=isinstance(backend, AerSimulator),
        solver_options=solver_options,
    )
    result = he.run()

    # step_4
    solution = postprocess(result, qubo_problem.is_feasible, he.optimization_monitor, postprocess_options)
    
    return solution

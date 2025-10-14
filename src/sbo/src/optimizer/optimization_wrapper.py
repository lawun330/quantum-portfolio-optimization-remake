# Copyright (C) 2024-2025 IBM Quantum
#
# This code is categorized as "existing" IBM asset
# as a part of Quantum Acceleration contract.
"""Wrapper for scipy optimization calls"""

from __future__ import annotations

import logging
from typing import Any, Callable, Union

import numpy as np
from qiskit.circuit import QuantumCircuit
from scipy.optimize import OptimizeResult, minimize

from .nft import nft_minimize
from .optimization_monitor import RefValueReached

LOGGER = logging.getLogger(__name__)


def run(  # pylint: disable=too-many-positional-arguments
    isa_ansatz: QuantumCircuit,
    optimization_fun: Callable[..., Any] | None = None,
    optimizer_x0: np.ndarray[Any, Any] | None = None,
    optimizer_args: tuple = (),
    optimizer_method: str | Callable = "nft",
    optimizer_callback: Callable[..., Any] | None = None,
    solver_options: dict | None = None,
) -> OptimizeResult:
    """
    Args:
        isa_ansatz: The ansatz circuit used for optimization.
        optimization_fun: The objective function to minimize. Defaults to None.
        optimizer_x0: Initial values for the parameters. Defaults to None.
        optimizer_args: Additional arguments to pass to the objective function. Defaults to ().
        optimizer_method: The optimization method to use. Can be "nft" or
            any other supported method by SciPy. Defaults to "nft".
        optimizer_callback: A callback function to execute after each
            iteration of the optimization process. Defaults to None.
        solver_options: Additional options to pass to the optimization method. Defaults to {}.

    Returns:
        The optimization result


    """
    LOGGER.info("run...")

    theta_initial = optimizer_x0
    LOGGER.debug("Using X0 %s", str(theta_initial))

    if theta_initial is None or len(theta_initial) == 0:
        theta_initial = (np.pi / 2) * np.ones(isa_ansatz.num_parameters)

    method: Union[str, Callable[..., Any]]
    method = optimizer_method
    if method == "nft":
        method = nft_minimize

    try:
        result = minimize(
            fun=optimization_fun,
            x0=theta_initial,
            args=optimizer_args,
            method=method,
            jac=None,
            hess=None,
            hessp=None,
            bounds=None,
            constraints=(),
            tol=None,
            callback=optimizer_callback,
            options=solver_options,
        )
    except RefValueReached as ex:
        result = OptimizeResult()
        result.x = ex.theta
        result.fun = ex.result
        result.nit = ex.nit
        result.nfev = ex.nfev
        result.success = True
        result.message = "Refvalue reached."

    return result

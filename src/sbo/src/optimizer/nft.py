# Copyright (C) 2024-2025 IBM Quantum
#
# This code is categorized as "existing" IBM asset
# as a part of Quantum Acceleration contract.
"""
Minimization methods with quantum. NFT
"""
from __future__ import annotations

import logging
from typing import Any, Callable, Tuple

import numpy as np
from scipy.optimize import OptimizeResult

LOGGER = logging.getLogger(__name__)

def round_angle_if_small(angle, threshold):
    if angle % (2*np.pi) < threshold:
        return (angle // (2*np.pi)) * (2*np.pi)
    if angle % (2*np.pi) > 2*np.pi-threshold:
        return (angle // (2*np.pi) + 1) * (2*np.pi)
    return angle

def _nft_update(val0, val1, val2, eps):  # Scipy compatible
    """
    Parameter update based on the NFT scheme
    """
    z0, z1, z3 = val0, val1, val2
    z2 = z1 + z3 - z0
    dr = eps * (z0 == z2)
    r = 0 if z1==z3 else ((z1 - z3) / ((z0 - z2) + dr))
    dw = np.arctan(float(r))
    dw += np.pi / 2 + np.pi / 2 * np.sign((z0 - z2) + dr)
    return dw


def nft_minimize(  # pylint: disable=too-many-positional-arguments
    fun: Callable[..., Any],
    x0: np.ndarray,
    args: tuple = (),  # (sampler, objective: callable, sampler_result_2_expectation:callable)
    jac: Callable | None = None,
    hess: Callable | None = None,
    hessp: Callable | None = None,
    bounds: None = None,
    constraints: Tuple | None = (),
    tol: float | None = None,
    callback: Callable | None = None,
    # algorithm_options
    max_epoch: int = 10,
    random_update: bool = True,
    epoch_start: int = 0,
    step_start: int = 0,
    idx_set_start: np.ndarray | None = None,
    # end alternate constructor
    **solver_options: dict | None,
):
    """
    Custom optimization method implementing NFT algorithm.
    An epoch allows the system to adjust and refine the parameters and
    the number of epochs can be adjusted. Each epoch consists of multiple
    iterations where the parameters are updated.

    Args:
        fun: Objective function to be minimized.
        x0: Initial guess.
        args: Extra arguments passed to the objective function.
        jac: Parameter to keep signature.
            NOT USED for NFT. Method for computing the gradient vector.
        hess: Parameter to keep signature.
            NOT USED for NFT. Method for computing the Hessian matrix.
        hessp: Parameter to keep signature.
            NOT USED for NFT. Hessian of the objective function times an arbitrary vector p.
        bounds: Parameter to keep signature.
            NOT USED for NFT. Bounds on variables for L-BFGS-B, TNC, SLSQP,
            Powell, and trust-constr methods.
        constraints (dict or sequence of dict, optional): Parameter to keep signature.
            NOT USED for NFT. Constraints definition.
        tol: Parameter to keep signature. NOT USED for NFT. Tolerance for termination.
        callback: Called after each iteration.
        max_epoch: Maximum number of epochs to run the optimization algorithm.
        random_update (bool):
            Whether to update parameters randomly or sequentially.
        epoch_start: epoch to start in case of warm start
        idx_set_start: index set for warm start
        step_start: initial step in warm start
        solver_options: A dictionary of solver options. It may include:
            - update_epsilon: the epsilon parameter in the update rule
            (if not provided, 1e-32 is used)
            - update_threshold: if the change at a given iteration is smaller than
            the threshold, no update is made
            (if not provided, 0. is used)
            - theta_threshold: if an angle of the variational form is smaller than
            the threshold, it is rounded to 0.
            (if not provided, 0. is used)
            In the paper: 0.06

    Returns:
        result (OptimizeResult):  The optimization result represented as a `OptimizeResult` object.

    """
    if solver_options is None:
        solver_options = {}

    # pylint: disable=unused-argument
    LOGGER.info("Using parameters: max_epoch %s", str(max_epoch))
    LOGGER.info("Using parameters: random_update %s", str(random_update))
    LOGGER.info("Using parameters: epoch_start %s", str(epoch_start))
    LOGGER.info("Using parameters: idx_set_start %s", str(idx_set_start))
    LOGGER.info("Using parameters: step_start %s", str(step_start))

    n_params = len(x0)
    theta = x0

    if step_start > 0 and idx_set_start is None:
        raise ValueError("idx_step_start must be provided when step_start is non-zero!")

    update_epsilon = solver_options.get("update_epsilon", 1e-32)
    update_threshold = solver_options.get("update_threshold", 0.)
    theta_threshold = solver_options.get("theta_threshold", 0.)
    nit = 1
    nfev = 0
    upd = None

    # Initial theta rounding
    theta = [round_angle_if_small(t, theta_threshold) for t in theta]

    for epoch in range(epoch_start, max_epoch):
        if idx_set_start is not None and epoch == epoch_start:
            idx_set = idx_set_start
        elif random_update:
            idx_set = np.random.permutation(n_params).astype(int)
        else:
            idx_set = np.arange(n_params).astype(int)

        for j, k in enumerate(idx_set):
            if epoch == epoch_start and j < step_start:
                continue  # Skips the first iterations
            
            new_core_eval = upd != 0.
            if new_core_eval:
                val0 = fun(theta, *args)
                nfev += 1
                nit += 1
            if callback:
                callback(theta, idx_set=idx_set, epoch=epoch, iter_in_epoch=j, update=upd, new_core_eval=new_core_eval)

            theta_1 = np.copy(theta)
            theta_1[k] += np.pi / 2
            val1 = fun(theta_1, *args)
            nfev += 1

            theta_2 = np.copy(theta)
            theta_2[k] -= np.pi / 2
            val2 = fun(theta_2, *args)
            nfev += 1

            upd = _nft_update(val0, val1, val2, update_epsilon)

            # threshold on theta
            theta_new = round_angle_if_small(theta[k] + upd, theta_threshold)
            upd = theta_new - theta[k]

            # threshold on update
            upd = round_angle_if_small(upd, update_threshold)
            theta[k] += upd

    new_core_eval = upd != 0.
    if new_core_eval:
        val0 = fun(theta, *args)
        nfev += 1
    if callback:
        callback(theta, idx_set=idx_set, epoch=epoch, iter_in_epoch=j, update=upd, new_core_eval=new_core_eval)

    result = OptimizeResult()
    result.x = theta
    result.fun = val0
    result.nit = nit
    result.nfev = nfev
    result.success = True
    result.message = (
        "Optimization terminated successfully."
    )
    return result

# Copyright (C) 2024-2025 IBM Quantum
#
# This code is categorized as "existing" IBM asset
# as a part of Quantum Acceleration contract.

"""Step 4, interpret solution."""
import logging
from typing import Callable, Any

from ...optimizer.local_search import repeated_local_search_general
from ...optimizer.optimization_monitor import OptimizationMonitor

from scipy.optimize import OptimizeResult

LOGGER = logging.getLogger(__name__)


def postprocess(
    solution: OptimizeResult,
    is_feasible: Callable[[Any], bool],
    optimization_monitor: OptimizationMonitor,
    options: dict | None = None,
) -> dict:
    """
    Args:
        target_mdl: The problem
        solution (OptimizeResult): Solution returned by optimization algorithm
        optimization_monitor (OptimizationMonitor): Optimization Monitor instance contains
            all values obtained in optimization process for cost and objective function and parameters.
        options: A dict with the postprocessing options, including
            - `local_search: Callable | None | bool`: `True` to activate standard local search,
            `False` or `None` to deactivate it, a `Callable` to provide a custom local search function
            Refer to the standard local search for its additional parameters.

    Returns:
        A dictionary containing the solution or the error message.
    """
    LOGGER.info("    STEP 4: postprocess...")

    if solution.success:
        val, x = optimization_monitor.objective_monitor.best_fx_x()
        # search
        if options is not None:
            search = options.get("local_search", None)
            if search is not None:
                if callable(search):
                    x, val, _, _, _ = search(
                        x, val, optimization_monitor.objective_monitor.cost, options
                    )
                else:
                    x, val, _, _, _ = repeated_local_search_general(
                        x, val, optimization_monitor.objective_monitor.cost, options
                    )
        # end local search

        return {
            "status": "success",
            "objective": float(val),
            "solution": x,
            "is_feasible": is_feasible(x),
            "execution_callback_count": optimization_monitor.callback_count,
            "execution_results": optimization_monitor.list_callback_res,
            "execution_f_value_best": optimization_monitor.list_callback_monitor_best,
            "message": solution.message,
        }

    return {
        "status": "fail",
        "execution_callback_count": optimization_monitor.callback_count,
        "execution_results": optimization_monitor.list_callback_res,
        "execution_f_value_best": optimization_monitor.list_callback_monitor_best,
        "message": solution.message,
    }

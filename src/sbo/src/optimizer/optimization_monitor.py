# Copyright (C) 2024-2025 IBM Quantum
#
# This code is categorized as "existing" IBM asset
# as a part of Quantum Acceleration contract.

"""Class to monitor the execution of optimization."""
from __future__ import annotations

import logging
from typing import Any, Callable

import numpy as np
import pickle
import asyncio

LOGGER = logging.getLogger(__name__)

def compress_x(bitstring: np.ndarray) -> int:
    return int(''.join([str(int(z)) for z in bitstring]), 2)

def uncompress_x(compressed: int, num_qubits: int) -> np.ndarray:
    return np.fromiter(map(int, "{0:0{num_qubits}b}".format(compressed, num_qubits=num_qubits)), dtype='float')

class RefValueReached(Exception):
    """Custom exception for stopping the algorithm when refvalue was found."""

    def __init__(self, theta: np.ndarray, result: float, nit: int, nfev: int):
        self.theta = theta
        self.result = result
        self.nit = nit
        self.nfev = nfev

    pass


class BestValueMonitor():
    """
    Keep best objective value result and parameters.
    """

    def __init__(self, f: Callable, store_all_x: bool = False):
        """
        Constructor for BestValueMonitor.
        Args:
            f: function to be wrapped.
        """
        self._f: Callable = f
        self._store_all_x: bool = store_all_x

        self.best_x: np.ndarray | None = None
        self.best_fx: float | None = None
        self.list_best_iter: list[int] = [] # iterations where best f(x) happens
        self.list_best_x: list[np.ndarray] = [] # x providing best f(x)
        self.list_best_fx: list[float] = [] # best values of f(x) found
        self.list_job_x: list[np.ndarray] = []
        self.list_job_cnt: list[int] = []
        self.list_job_fx: list[float] = []
        self.list_x: list[list[np.ndarray]] = []
        self.list_cnt: list[list[int]] = []
        self.list_fx: list[list[float]] = []
        self.iter_best_x: np.array = None # best x of the current iteration
        self.iter_best_fx: float = None # best fx of the current iteration
        self.iter_fx_evals: int = 0 # function evals in current iteration


    def cost(self, x: np.ndarray[Any, Any], *args: dict, iter=-1, cnt=-1):
        """Executes the actual simulation and returns the result, while
        keeping track of best value for the result
        Args:
            x (np.array): parameters for the function
            *args: additional arguments
        Returns:
            result of the function call
        """
        # the actual evaluation of the function
        result = self._f(x, *args)
        self.iter_fx_evals += 1

        if self._store_all_x:
            self.list_job_x.append(x)
            self.list_job_cnt.append(cnt)
            self.list_job_fx.append(result)

        if self.iter_best_fx is None or result < self.iter_best_fx:
            self.iter_best_fx = result
            self.iter_best_x = x
        
        if self.best_fx is None or result < self.best_fx:
            self.best_fx = result
            self.best_x = x
            self.list_best_iter.append(iter)
            self.list_best_fx.append(result)
            self.list_best_x.append(x)

        return result

    def best_fx_x(self):
        """Returns best seen result in calls

        Returns:
            tuple: best result and best parameters
        """
        if self.best_fx is None:
            raise RuntimeError("function is not yet optimized")

        return self.best_fx, self.best_x


class OptimizationMonitor:
    """Avoid repeated calls for callback
    Stores history
    """

    def __init__(  # pylint: disable=too-many-positional-arguments
        self,
        function: Callable,
        objective_monitor: BestValueMonitor,
        verbose: str | None = None,
        refvalue: float | None = None,
        file_name: str | None = None,
        iter_file_path_prefix: str | None = None
    ):
        """
        Args:
            function: function to be monitored
            objective_monitor: monitor for the objective function
            verbose:  Default None - > no log displayed
                "cost" -> cost function calls are displayed
                "callback" -> callback function calls are displayed
                "callback_all" -> a summary of the call including cost and objective
                function result is displayed
            refvalue: Value for the cost function where we stop the execution.
            file_name: File to log processing data.
            iter_file_path_prefix: File path for iteration file, typically in the
                form 'path\\xxx'. It will be completed as 'path\\xxx_{nit}.pkl'.
                Set to None to avoid writing iteration file.
        """
        self._f = function  # actual cost function
        if verbose is None:
            self._verbose = ""  # for easy comparison
        else:
            self._verbose = verbose
        self.refvalue = refvalue
        self.calls_count = 0  # how many times f has been called
        self.callback_count = (
            0  # number of times callback has been called, also measures iteration count
        )
        self.objective_monitor = (
            objective_monitor  # monitor the nester call of objective calculation
        )

        self.list_calls_inp: list[np.ndarray] = []  # input of all calls
        self.list_calls_res: list[float] = []  # result of all calls
        self.list_callback_inp: list[np.ndarray] = (
            []
        )  # only appends inputs on callback, as such they correspond to the iterations
        self.list_callback_res: list[float] = (
            []
        )  # only appends results on callback, as such they correspond to the iterations
        self.list_callback_monitor_best: list[float] = []
        self.iter_best_x: list[np.ndarray] = []
        self.iter_best_fx: list[float] = []
        self.iter_fx_evals: list[int] = []
        self.logger = None
        if file_name is not None:
            self.logger = logging.getLogger("OptimizationMonitor")
            self.logger.setLevel(logging.INFO)  # Set log level for ClassB

            handler = logging.FileHandler(file_name)
            handler.setFormatter(
                logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
            )
            self.logger.addHandler(handler)
        
        self._iter_file_path_prefix = iter_file_path_prefix


    def cost(self, theta: np.ndarray, *args: dict):
        """Executes the actual simulation and returns the result, while
        updating the lists too. Pass to optimizer without arguments or
        parentheses.
        Args:
            theta (np.array): parameters for the function
            *args: additional arguments
        Returns:
            result of the function call
        """
        if self._verbose == "cost":
            print(f"cost: {self.calls_count:10d}", theta)
        # the actual evaluation of the function
        result = self._f(theta, *args)

        self.list_calls_inp.append(theta)
        self.list_calls_res.append(result)
        self.calls_count += 1

        return result

    async def write_iter(file_name, data):
        # compressing list_x
        # to uncompress, use [[np.fromiter(map(int, "{0:0{num_qubits}b}".format(y, num_qubits=ansatz_.num_qubits)), dtype='uint8') for y in x] for x in compressed]
        # data['list_x'] = [[int(''.join([str(int(z)) for z in y]), 2) for y in x] for x in data['list_x']]
        data['list_x'] = [[compress_x(y) for y in x] for x in data['list_x']]

        with open(file_name, 'wb') as f:
            pickle.dump(data, f)

    def callback(self, theta: np.ndarray, *args, **kwargs: dict):
        """
        Callback function that can be used by optimizers of scipy.optimize.
        Args:
            theta (np.array): parameters for the function
            *args: additional arguments
            **kwargs: additional arguments
        """
        LOGGER.info("optimizer internal status: %s %s", args, kwargs)

        if self._iter_file_path_prefix is not None:
            file_name = f'{self._iter_file_path_prefix}_{self.number_of_iterations()}.pkl'
            data = {
                'optimizer_internal_status': args,
                'optimizer_internal_status_dict': kwargs,
                'list_x': self.objective_monitor.list_x,
                'list_cnt': self.objective_monitor.list_cnt,
                'list_fx': self.objective_monitor.list_fx,
                }
            asyncio.run(OptimizationMonitor.write_iter(file_name, data))
        self.objective_monitor.list_x = []
        self.objective_monitor.list_fx = []
        self.objective_monitor.list_cnt = []
        self.iter_best_x.append(self.objective_monitor.iter_best_x)
        self.iter_best_fx.append(self.objective_monitor.iter_best_fx)
        self.iter_fx_evals.append(self.objective_monitor.iter_fx_evals)
        self.objective_monitor.iter_best_x = None
        self.objective_monitor.iter_best_fx = None
        self.objective_monitor.iter_fx_evals = 0


        if self._verbose == "callback":
            print(f"cabk: {self.callback_count:10d}", theta)
        theta = np.atleast_1d(theta)
        found = False
        # search backwards in input list for input corresponding to theta
        i = 0
        for i, theta0 in reversed(list(enumerate(self.list_calls_inp))):
            theta0 = np.atleast_1d(theta0)
            if np.allclose(theta0, theta):
                found = True
                break
        if found:
            self.list_callback_inp.append(theta)
            self.list_callback_res.append(self.list_calls_res[i])
            self._add_best_value(theta, i)
        else:
            LOGGER.info("Unexpected behavior: Result of optimizer cost function call not found.")
            self.list_callback_inp.append(self.list_calls_inp[-1])
            self.list_callback_res.append(self.list_calls_res[-1])
            self._add_best_value(theta, i)

        self.callback_count += 1

        # Headers in the first call
        if self.callback_count == 1:
            s0 = " Iteration\t  Calls   \t              Cost "
            for j, _ in enumerate(theta):
                tmp = f"Comp-{j+1}"
                s0 += f"\t{tmp:12s}"
            if self.objective_monitor is not None:
                value, x_array = self.objective_monitor.best_fx_x()
                s0 += "\tObjective   \tBitstring \tParams"
            if self._verbose == "callback_all":
                print(s0)
            if self.logger is not None:
                self.logger.info(s0)

        s1 = f"{self.callback_count:10d}\t{self.calls_count:10d}\t\
                    {self.list_callback_res[-1]:12.5e}\t"
        for comp in theta:
            s1 += f"\t{comp:12.5e}"
        if self.objective_monitor is not None:
            # Assuming self.objective_monitor.best_x() returns a tuple (value, x_array)
            value, x_array = self.objective_monitor.best_fx_x()
            s1 += f"\t{value}   \t{x_array}"
            s1 += str(args)
            s1 += str(kwargs)
        if self._verbose == "callback_all":
            print(s1)
        if self.logger is not None:
            self.logger.info(s1)

    def _add_best_value(self, theta: np.ndarray, i: int):
        if self.objective_monitor is not None:
            best_fx = self.objective_monitor.best_fx_x()[0]
            self.list_callback_monitor_best.append(best_fx)
            if self.refvalue is not None:
                if np.isclose(best_fx, np.float64(self.refvalue)) or best_fx < self.refvalue:
                    raise RefValueReached(
                        theta,
                        self.list_calls_res[i],
                        self.number_of_iterations(),
                        self.number_of_function_evaluations(),
                    )

    def best_seen_result(self):
        """
        Will check that the optimization run and return best result in callback.
        Returns:
          Best seen result in callback"""
        if self.callback_count == 0:
            raise RuntimeError("function is not yet optimized")

        min_index = self.list_callback_res.index(min(self.list_callback_res))
        min_value = self.list_callback_res[min_index]
        corresponding_parameters = self.list_callback_inp[min_index]

        return min_value, corresponding_parameters

    def number_of_function_evaluations(self):
        """
        Number of times cost function was called by the optimization algorithm.
        Returns:
            Number of times cost function was called."""
        return self.calls_count

    def number_of_iterations(self):
        """
        Number of callbacks called by the optimization algorithm.
        Returns:
            Number of times cost function was called."""
        return self.callback_count

# Copyright (C) 2024-2025 IBM Quantum
#
# This code is categorized as "existing" IBM asset
# as a part of Quantum Acceleration contract.

"""Step 3, run on hardware."""
from __future__ import annotations

import logging
from typing import Any, Callable, Tuple, Optional, Union, Dict

import numpy as np
import time
from qiskit import QuantumCircuit
from qiskit.providers import BackendV2
from qiskit.result import Result
from qiskit_ibm_runtime import SamplerV2, Session, SamplerOptions
from qiskit.providers.exceptions import QiskitError
from scipy.optimize import OptimizeResult
from numba import jit

from ...optimizer.optimization_monitor import BestValueMonitor, OptimizationMonitor
from ...optimizer.optimization_wrapper import run as run_wrapper

LOGGER = logging.getLogger(__name__)


class HardwareExecutor:

    def __init__(
        self,
        objective_fun: Callable[..., float],
        backend: BackendV2,
        isa_ansatz: QuantumCircuit,
        optimizer_theta0: np.ndarray[Any, Any] | None = None,
        optimizer_method: str | Callable = "nft",
        sampler_result_to_aggregate_objective: Callable[[Result], float] | None = None,
        refvalue: float | None = None,
        sampler_options: Optional[Union[Dict, SamplerOptions]] = {},
        use_session: bool = True,
        verbose: str | None = None,
        file_name: str | None = None,
        store_all_x: bool = False,
        iter_file_path_prefix: str | None = None,
        solver_options: dict | None = None,
        max_retries: int = 10,
        run_id: str | None = None,
    ):
        self.backend = backend
        self.isa_ansatz = isa_ansatz
        self.optimizer_theta0 = optimizer_theta0
        self.optimizer_method = optimizer_method
        self.refvalue = refvalue
        self.sampler_options = sampler_options
        self.verbose = verbose
        self.file_name = file_name
        self.solver_options = solver_options
        self.max_retries = max_retries
        self.run_id = str(int(time.time())) if run_id is None else run_id

        self.objective_monitor = BestValueMonitor(objective_fun, store_all_x)

        self.optimization_monitor = OptimizationMonitor(
            self.calc_aggregate_objective,
            self.objective_monitor,
            verbose=verbose,
            refvalue=refvalue,
            file_name=file_name,
            iter_file_path_prefix=iter_file_path_prefix,
        )

        self.job_ids: list[str] = []

        if sampler_result_to_aggregate_objective is None:
            self._sampler_result_to_aggregate_objective = self._sampler_result_to_cvar

        if use_session:
            self._run_method = self._run_with_session
        else:
            self._run_method = self._run_with_jobs

    def _run_with_sampler(self) -> OptimizeResult:
        self.sampler.options.environment.job_tags = [self.run_id, f'{self.run_id}_{self.optimization_monitor.number_of_iterations()}']
        result = run_wrapper(
            isa_ansatz=self.isa_ansatz,
            optimizer_x0=self.optimizer_theta0,
            optimization_fun=self.optimization_monitor.cost,
            optimizer_args=(),
            optimizer_method=self.optimizer_method,
            optimizer_callback=self.optimization_monitor.callback,
            solver_options=self.solver_options,
        )

        return result

    def _run_with_session(self) -> OptimizeResult:
        with Session(backend=self.backend) as session:
            self.sampler = SamplerV2(mode=session, options=self.sampler_options)
            return self._run_with_sampler()

    def _run_with_jobs(self) -> OptimizeResult:
        self.sampler = SamplerV2(mode=self.backend, options=self.sampler_options)
        return self._run_with_sampler()

    def run(self) -> OptimizeResult:
        try:
            result = self._run_method()
        except QiskitError as error:
            # Return a partial result
            result = OptimizeResult()
            gtheta, theta = self.optimization_monitor.best_seen_result()
            result.x = theta
            result.fun = gtheta
            result.nit = self.optimization_monitor.number_of_iterations()
            result.fevals = self.optimization_monitor.number_of_function_evaluations()
            result.success = False
            result.message = error.message

        return result
    
    def submit_job(self, theta, remaining_attempts: int):
        self.sampler.options
        job = self.sampler.run([(self.isa_ansatz, theta)])
        job_id = job.job_id() if callable(job.job_id) else job.job_id
        self.job_ids.append(job_id)
        try:
            return job.result()
        except QiskitError as error:
            if remaining_attempts > 0:
                LOGGER.warning('job %s failed, retrying (%d remaining attempts)', job_id, remaining_attempts)
                return self.submit_job(theta, remaining_attempts=remaining_attempts-1)
            else:
                raise error


    def calc_aggregate_objective(self, theta: np.ndarray) -> float:
        """
        Runs the parameterized circuit and returns cVAR value
        Args:
            theta: The input parameters for the circuit.

        Returns:
            float: The calculated cVAR value.
        """
        self.optimization_monitor.objective_monitor.list_x.append(self.optimization_monitor.objective_monitor.list_job_x)
        self.optimization_monitor.objective_monitor.list_cnt.append(self.optimization_monitor.objective_monitor.list_job_cnt)
        self.optimization_monitor.objective_monitor.list_fx.append(self.optimization_monitor.objective_monitor.list_job_fx)
        self.optimization_monitor.objective_monitor.list_job_x = []
        self.optimization_monitor.objective_monitor.list_job_cnt = []
        self.optimization_monitor.objective_monitor.list_job_fx = []
        result = self.submit_job(theta, self.max_retries)

        aggr_obj = self._sampler_result_to_aggregate_objective(result)
        return aggr_obj
    
    @staticmethod
    @jit
    def calc_cvar(sorted_count: np.ndarray, sorted_fx: np.ndarray, ak: int) -> float:
        count_cumsum = 0
        cvar = 0
        for idx, cnt in np.ndenumerate(sorted_count):
            count_cumsum += cnt
            cvar += cnt * sorted_fx[idx]
            if count_cumsum >= ak:
                break

        cvar -= sorted_fx[idx]*(count_cumsum-ak)
        return cvar / ak

    def _sampler_result_to_cvar(self, result: Result) -> float:
        """
        Converts the results of a Qiskit sampler run into an cvar objective value
        using the given objective function.

        Args:
        result: The result of a Qiskit sampler run.

        Returns:
            float: The expectation value calculated from the results of the sampler run.
        """
        alpha = self.solver_options.get("alpha", 1.0)

        counts = result[0].data.meas.get_counts()

        # bin_list = list(counts.keys())
        # obj_val_list = []

        # for bins in bin_list:
        #     x = np.array(list(bins)).astype(float)
        #     x = np.flip(x)
        #     obj_val = self.objective_monitor.cost(x, iter=self.optimization_monitor.callback_count)

        #     for _ in range(0, counts[bins]):
        #         obj_val_list.append(obj_val)

        # len_list = len(obj_val_list)
        # ak = np.ceil(len_list * alpha)
        # sorted_obj = np.sort(obj_val_list)
        # old_cvar = np.sum(sorted_obj[0 : int(ak)]) / ak

        dtype = [('fx', float), ('cnt', int)]
        vals = np.array([
            (
                self.objective_monitor.cost(np.array(list(bins[::-1]), dtype=float), iter=self.optimization_monitor.callback_count, cnt=cnt), 
                cnt
            )
            for bins, cnt in counts.items()
            ], dtype=dtype)
        vals.sort(kind='heapsort', order='fx')
        
        shots = result[0].data.meas.num_shots
        ak = int(np.ceil(shots * alpha))

        cvar = HardwareExecutor.calc_cvar(vals['cnt'], vals['fx'], ak)

        # assert abs(old_cvar - cvar) < 1e-6
        return cvar

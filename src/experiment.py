from pathlib import Path
ROOT = Path(__file__).parent.parent

from dataclasses import dataclass, asdict, field
from typing_extensions import Self
import numpy as np
import pickle
import pandas as pd
from qiskit import QuantumCircuit

from .sbo.src.optimizer.optimization_monitor import OptimizationMonitor
from .sbo.src.optimizer.optimization_wrapper import OptimizeResult

@dataclass
class Experiment:
    experiment_id: str
    local_search_doe: str | None
    ansatz: str
    ansatz_params: dict
    theta_initial: str
    device: str
    optimizer: str
    alpha: float | None
    theta_threshold: float | None
    lp_file: str
    shots: int
    refx: list[int] | None
    refvalue: float | None
    classical_hw: str
    step3_time: float
    step4_time: float | None
    step3_job_ids: list[str]
    step3_fx_evals: int
    step3_result_success: bool
    step3_result_message: str
    step3_result_best_x: np.ndarray
    step3_result_best_fx: float
    step4_num_epochs: list[int] | None
    step4_fx_evals: list[int] | None
    step4_result_best_x: np.ndarray | None
    step4_result_best_fx: float | None
    step3_monitor_iter_thetas: list[np.ndarray]
    step3_monitor_iter_gtheta: list[float]
    step3_monitor_iter_best_fx: list[np.ndarray]
    step3_monitor_calls_thetas: list[np.ndarray]
    step3_monitor_calls_gtheta: list[float]
    step3_iter_best_x: list[np.ndarray]
    step3_iter_best_fx: list[np.ndarray]
    step3_iter_fx_evals: list[int]
    step4_iter_best_fx: list[float] | None
    notes: list[str] = field(default_factory=list)

    def improvement_iterations(self):
        return {i+1:self.step3_monitor_iter_best_fx[i+1]  for i in range(len(self.step3_monitor_iter_best_fx)-1) if self.monitor_list_callback_monitor_best[i] != self.monitor_list_callback_monitor_best[i+1]}

    def last_improvement_iteration(self):
        return sum(np.array(self.step3_monitor_iter_best_fx) != self.step3_monitor_iter_best_fx[-1])
    
    def step3_x_diff(self):
        return sum(np.abs(self.refx-self.step3_result_best_x))
    
    def step3_x_hamming_weight(self):
        return sum(np.abs(self.step3_result_best_x))
    
    def step3_rel_gap(self):
        return (self.step3_result_best_fx-self.refvalue)/ self.refvalue
    
    def step3_num_thetas(self):
        return None if self.step3_monitor_iter_thetas is None else len(self.step3_monitor_iter_thetas[0])
    
    def has_step4(self):
        return self.step4_time is not None

    def step4_x_diff(self):
        return None if self.step4_result_best_x is None else sum(np.abs(self.refx-self.step4_result_best_x))

    def step4_x_hamming_weight(self):
        return None if self.step4_result_best_x is None else sum(np.abs(self.step4_result_best_x))
    
    def step4_rel_gap(self):
        return None if self.step4_result_best_fx is None else (self.step4_result_best_fx-self.refvalue)/ self.refvalue

    @staticmethod
    def read_experiment(experiment_id) -> list[dict]:
        path = Path(f'{ROOT}/data/{experiment_id}')

        with open(path, 'rb') as f:
            data: dict = pickle.load(f)
        xp = Experiment(**data)
        
        return xp

    @staticmethod
    def read_experiments(experiment_set='1/31bonds/') -> list[dict]:
        pathlist = Path(f'{ROOT}/data/{experiment_set}').glob(f'**/exp*.pkl')

        all_experiments = []
        for path in pathlist:
            with open(path, 'rb') as f:
                data: dict = pickle.load(f)
            if len(data) == 0: continue
            xp = Experiment(**data)

            all_experiments.append(xp)

        return all_experiments
    
    @staticmethod
    def df_experiments(all_experiments: list[Self], **kwargs) -> pd.DataFrame:
        all_experiments_dict = []
        for xp in all_experiments:
            xp_dict = asdict(xp)
            # Flatten records whose type is dict
            pop_key_list = []
            update_dict = {}
            for k,v in xp_dict.items():
                if isinstance(v, dict):
                    update_dict.update({f'{k}_{k1}':v1 for k1, v1 in v.items()})
                    pop_key_list.append(k)
            xp_dict.update(update_dict)
            for k in pop_key_list:
                xp_dict.pop(k)

            xp_dict.update({
                'last_improvement_iter': xp.last_improvement_iteration(),
                'step3_x_diff': xp.step3_x_diff(),
                'step3_x_hamming_weight': xp.step3_x_hamming_weight(),
                'step3_rel_gap': xp.step3_rel_gap(),
                'step3_num_thetas': xp.step3_num_thetas(),
                'has_step4': xp.has_step4(),
                'step4_x_diff': xp.step4_x_diff(),
                'step4_x_hamming_weight': xp.step4_x_hamming_weight(),
                'step4_rel_gap': xp.step4_rel_gap(),
            })
            all_experiments_dict.append(xp_dict)
    
        df = pd.DataFrame(all_experiments_dict)
        
        return Experiment.filter_experiments(df, **kwargs)
    
    @staticmethod
    def filter_experiments(df: pd.DataFrame, **kwargs) -> pd.DataFrame:
        df = df.copy()
        for k,v in kwargs.items():
            if not isinstance(v, list):
                v = [v]
            df = df[df[k].isin(v)]
        return df
 
    @staticmethod
    def get_current_classical_hw():
        import platform
        return platform.node()
    
    @staticmethod
    def from_step3(experiment_id,
                   ansatz, ansatz_params, theta_initial, device, optimizer, alpha, theta_threshold, lp_file, shots, refx, refvalue,
                   classical_hw, step3_time, step3_job_ids,
                   result: OptimizeResult, optimization_monitor: OptimizationMonitor) -> Self:
        return Experiment(
            experiment_id=experiment_id,
            local_search_doe=None,
            ansatz=ansatz,
            ansatz_params=ansatz_params,
            theta_initial=theta_initial,
            device=device,
            optimizer=optimizer,
            alpha=alpha,
            theta_threshold=theta_threshold,
            lp_file=lp_file,
            shots=shots,
            refx=refx,
            refvalue=refvalue,
            classical_hw=classical_hw,
            step3_time=step3_time,
            step4_time=None,
            step3_job_ids=step3_job_ids,
            step3_fx_evals=optimization_monitor.calls_count,
            step3_result_success=result.success,
            step3_result_message=result.message,
            step3_result_best_x=optimization_monitor.objective_monitor.best_x,
            step3_result_best_fx=optimization_monitor.objective_monitor.best_fx,
            step4_num_epochs=None,
            step4_fx_evals=None,
            step4_result_best_x=None,
            step4_result_best_fx=None,
            step3_monitor_iter_thetas=optimization_monitor.list_callback_inp,
            step3_monitor_iter_gtheta=optimization_monitor.list_callback_res,
            step3_monitor_iter_best_fx=optimization_monitor.list_callback_monitor_best,
            step3_monitor_calls_thetas=optimization_monitor.list_calls_inp,
            step3_monitor_calls_gtheta=optimization_monitor.list_calls_res,
            step3_iter_best_x=optimization_monitor.iter_best_x,
            step3_iter_best_fx=optimization_monitor.iter_best_fx,
            step3_iter_fx_evals=optimization_monitor.iter_fx_evals,
            step4_iter_best_fx=None
        )
@dataclass
class ServerlessExperiment:
    experiment_id: str
    classical_hw: str
    step3_time: float
    step3_job_ids: list[str]
    step3_fx_evals: int
    step3_result_success: bool
    step3_result_message: str
    step3_result_best_x: np.ndarray
    step3_result_best_fx: float
    step3_monitor_iter_thetas: list[np.ndarray]
    step3_monitor_iter_gtheta: list[float]
    step3_monitor_iter_best_fx: list[np.ndarray]
    step3_monitor_calls_thetas: list[np.ndarray]
    step3_monitor_calls_gtheta: list[float]

    @staticmethod
    def from_serverless(experiment_id,
                   classical_hw, step3_time, step3_job_ids,
                   result: OptimizeResult, optimization_monitor: OptimizationMonitor) -> Self:
        
        return ServerlessExperiment(
            experiment_id=experiment_id,
            classical_hw=classical_hw,
            step3_time=step3_time,
            step4_time=None,
            step3_job_ids=step3_job_ids,
            step3_fx_evals=optimization_monitor.calls_count,
            step3_result_success=result.success,
            step3_result_message=result.message,
            step3_result_best_x=optimization_monitor.objective_monitor.best_x,
            step4_num_epochs=None,
            step4_fx_evals=None,
            step4_result_best_x=None,
            step4_result_best_fx=None,
            step3_result_best_fx=optimization_monitor.objective_monitor.best_fx,
            step3_monitor_iter_thetas=optimization_monitor.list_callback_inp,
            step3_monitor_iter_gtheta=optimization_monitor.list_callback_res,
            step3_monitor_iter_best_fx=optimization_monitor.list_callback_monitor_best,
            step3_monitor_calls_thetas=optimization_monitor.list_calls_inp,
            step3_monitor_calls_gtheta=optimization_monitor.list_calls_res,
            step4_monitor_iter_best_fx=None
        )
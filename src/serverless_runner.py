import pickle as pkl
import time
import dataclasses
from importlib.util import find_spec
from qiskit_ibm_runtime import QiskitRuntimeService
from qiskit_serverless import get_arguments, save_result
import logging


from step_1 import model_to_obj
from experiment import Experiment, ServerlessExperiment
from sbo.src.patterns.building_blocks.step_3 import HardwareExecutor
from sbo.src.utils.lp_utils import (
    load_quadratic_program_from_lp_str,
    load_quadratic_program_from_lp_str_cplex,
)

arguments = get_arguments()

experiment_id_with_exec = arguments.get('experiment_id_with_exec')
lp_content = arguments.get('lp_content')
isa_ansatz = arguments.get('isa_ansatz')
theta_initial_ = arguments.get('theta_initial_')
optimizer = arguments.get('optimizer')
refval = arguments.get('refval')
shots = arguments.get('shots')
max_epoch = arguments.get('max_epoch')
alpha = arguments.get('alpha')
device = arguments.get('device')
instance = arguments.get('instance')

LOGGER = logging.getLogger(__name__)

CPLEX_AVAILABLE = False
if find_spec("cplex") is not None:
    CPLEX_AVAILABLE = True

if CPLEX_AVAILABLE:
    LOGGER.info("Using Cplex parser")
    model = load_quadratic_program_from_lp_str_cplex(lp_content)
else:
    LOGGER.info("Using local parser")
    model = load_quadratic_program_from_lp_str(lp_content)

obj_fn = model_to_obj(model)

service = QiskitRuntimeService()
backend = service.backend(device, instance)

t = time.time()
he = HardwareExecutor(
    objective_fun=obj_fn,
    backend=backend,
    isa_ansatz=isa_ansatz,
    optimizer_theta0=theta_initial_,
    optimizer_method=optimizer,
    refvalue=refval,
    sampler_options={'default_shots':shots},
    use_session=False,
    iter_file_path_prefix='data/',
    store_all_x=False,
    solver_options={"max_epoch": max_epoch, "alpha": alpha},
)
result = he.run()
step3_time = time.time() - t

out = ServerlessExperiment.from_serverless(
    experiment_id_with_exec,
    Experiment.get_current_classical_hw(), step3_time, he.job_ids,
    result, he.optimization_monitor
)

out_file = f'data/out.pkl'
with open(out_file, 'bw') as f:
    pkl.dump(dataclasses.asdict(out), f)

save_result(dataclasses.asdict(out))
from qiskit_ibm_catalog import QiskitServerless, QiskitFunction
from pathlib import Path
ROOT = Path(__file__).parent.parent.parent.parent

# Authenticate to the remote cluster and submit the pattern for remote execution
serverless = QiskitServerless()

remote_step3 = QiskitFunction(
    title="execute_on_hw",
    entrypoint="serverless_runner.py",
    working_dir=str(ROOT / 'src'),
    # dependencies=['docplex', 'scipy']
)

serverless.upload(remote_step3)

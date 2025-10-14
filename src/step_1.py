import numpy as np
import docplex.mp
import docplex.mp.model
import docplex.mp.constants
import numpy as np
import docplex.mp
import docplex.mp.model
import docplex.mp.model_reader
import docplex.mp.solution
from qiskit.circuit.library import TwoLocal, NLocal, RYGate
from qiskit.circuit import QuantumCircuit, ParameterVector
from qiskit.circuit.library.standard_gates import get_standard_gate_name_mapping
from qiskit_aer import AerSimulator
from qiskit_ibm_runtime import QiskitRuntimeService
from qiskit.providers.backend import BackendV2
from qiskit.transpiler import CouplingMap

import numba
from numba import jit

# from line_profiler import profile

from scipy.sparse import csr_array

def model_to_obj_dense(model: docplex.mp.model.Model):
    num_vars = model.number_of_binary_variables
    num_ctr = model.number_of_constraints
    print(num_vars, num_ctr)

    # Parsing objective under assumption:
    # - the objective is in the form quadratic + linear + c
    # Output: Q (as a dense matrix) and c such that      objective = x^T Q x + c

    Q = np.zeros((num_vars, num_vars))
    c = model.objective_expr.get_constant()

    for i, dvari in enumerate(model.iter_variables()):
        for j, dvarj in enumerate(model.iter_variables()):
            Q[i,j] = model.objective_expr.get_quadratic_coefficient(dvari, dvarj) / 2
            if i == j:
                Q[i,i] = model.objective_expr.get_quadratic_coefficient(dvari, dvari) + model.objective_expr.linear_part.get_coef(dvari)

    # Parsing constraints under the assumption:
    # - they are all linear inequalities *** it could be generalized to equalities!
    # Retrieving A and b such that constraints write as    A x - b ≥ 0.

    A = np.zeros((num_ctr, num_vars))
    b = np.zeros(num_ctr)

    for i, ctr in enumerate(model.iter_constraints()):
        sense = 1 if ctr.sense == docplex.mp.constants.ComparisonType.GE else -1
        for j, dvarj in enumerate(model.iter_variables()):
            A[i,j] = sense * ctr.lhs.get_coef(dvarj)
        b[i] = sense * ctr.rhs.get_constant()

    # Rescale constraints so that the minimum coefficient of a variable in each constraint is 1 (in abs)

    min_A_by_row = np.zeros(num_ctr)

    for i,row in enumerate(A):
        min_A_by_row[i] = np.min(np.abs(row[np.nonzero(row)]))

    A = A / min_A_by_row.reshape(num_ctr, 1)
    b = b / min_A_by_row

    # Translate constraints into obj terms under the following assumptions:
    # - minimization problem
    # - all vars are bin (or integer)
    # - each coef in constraints is ≥ 1 (in abs)
    # Remark: the resulting unconstr_obj_fn is not polynomial (contains maximum), and it's designed to be used in sampling VQE

    max_obj = np.sum(Q, where=Q>0)
    min_obj = np.sum(Q, where=Q<0)
    penalty = (max_obj-min_obj) * 1.1

    @jit
    def obj_fn_embedding_constraints(x):
        return x @ Q @ x + c + penalty * np.sum(np.maximum(b - A @ x, 0)**2)

    return obj_fn_embedding_constraints


def model_to_obj_sparse(model: docplex.mp.model.Model):
    num_vars = model.number_of_binary_variables
    num_ctr = model.number_of_constraints
    print(num_vars, num_ctr)

    # Parsing objective under assumption:
    # - the objective is in the form quadratic + linear + c
    # Output: Q (as a dense matrix) and c such that      objective = x^T Q x + c

    Q = np.zeros((num_vars, num_vars))
    c = model.objective_expr.get_constant()

    for i, dvari in enumerate(model.iter_variables()):
        for j, dvarj in enumerate(model.iter_variables()):
            if i > j: continue
            Q[i,j] = model.objective_expr.get_quadratic_coefficient(dvari, dvarj)
            if i == j:
                Q[i,i] += model.objective_expr.linear_part.get_coef(dvari)

    # Parsing constraints under the assumption:
    # - they are all linear inequalities *** it could be generalized to equalities!
    # Retrieving A and b such that constraints write as    A x - b ≥ 0.

    A = np.zeros((num_ctr, num_vars))
    b = np.zeros(num_ctr)

    for i, ctr in enumerate(model.iter_constraints()):
        sense = 1 if ctr.sense == docplex.mp.constants.ComparisonType.GE else -1
        for j, dvarj in enumerate(model.iter_variables()):
            A[i,j] = sense * ctr.lhs.get_coef(dvarj)
        b[i] = sense * ctr.rhs.get_constant()

    # Rescale constraints so that the minimum coefficient of a variable in each constraint is 1 (in abs)

    min_A_by_row = np.zeros(num_ctr)

    for i,row in enumerate(A):
        min_A_by_row[i] = np.min(np.abs(row[np.nonzero(row)]))

    A = A / min_A_by_row.reshape(num_ctr, 1)
    b = b / min_A_by_row

    # Translate constraints into obj terms under the following assumptions:
    # - minimization problem
    # - all vars are bin (or integer)
    # - each coef in constraints is ≥ 1 (in abs)
    # Remark: the resulting unconstr_obj_fn is not polynomial (contains maximum), and it's designed to be used in sampling VQE

    max_obj = np.sum(Q, where=Q>0)
    min_obj = np.sum(Q, where=Q<0)
    penalty = (max_obj-min_obj) * 1.1

    sparseQ = csr_array(Q)
    sparseA = csr_array(A)

    @jit
    def obj_fn_embedding_constraints(x):
        return x @ (sparseQ @ x) + c + penalty * np.sum(np.maximum(b - sparseA @ x, 0)**2)

    return obj_fn_embedding_constraints


def model_to_obj_sparse_numba(model: docplex.mp.model.Model):
    num_vars = model.number_of_binary_variables
    num_ctr = model.number_of_constraints
    print(num_vars, num_ctr)

    # Parsing objective under assumption:
    # - the objective is in the form quadratic + linear + c
    # Output: Q (as a dense matrix) and c such that      objective = x^T Q x + c

    Q = np.zeros((num_vars, num_vars))
    c = model.objective_expr.get_constant()

    for i, dvari in enumerate(model.iter_variables()):
        for j, dvarj in enumerate(model.iter_variables()):
            if i > j: continue
            Q[i,j] = model.objective_expr.get_quadratic_coefficient(dvari, dvarj)
            if i == j:
                Q[i,i] += model.objective_expr.linear_part.get_coef(dvari)

    # Parsing constraints under the assumption:
    # - they are all linear inequalities *** it could be generalized to equalities!
    # Retrieving A and b such that constraints write as    A x - b ≥ 0.

    A = np.zeros((num_ctr, num_vars))
    b = np.zeros(num_ctr)

    for i, ctr in enumerate(model.iter_constraints()):
        sense = 1 if ctr.sense == docplex.mp.constants.ComparisonType.GE else -1
        for j, dvarj in enumerate(model.iter_variables()):
            A[i,j] = sense * ctr.lhs.get_coef(dvarj)
        b[i] = sense * ctr.rhs.get_constant()

    # Rescale constraints so that the minimum coefficient of a variable in each constraint is 1 (in abs)

    min_A_by_row = np.zeros(num_ctr)

    for i,row in enumerate(A):
        min_A_by_row[i] = np.min(np.abs(row[np.nonzero(row)]))

    A = A / min_A_by_row.reshape(num_ctr, 1)
    b = b / min_A_by_row

    # Translate constraints into obj terms under the following assumptions:
    # - minimization problem
    # - all vars are bin (or integer)
    # - each coef in constraints is ≥ 1 (in abs)
    # Remark: the resulting unconstr_obj_fn is not polynomial (contains maximum), and it's designed to be used in sampling VQE

    max_obj = np.sum(Q, where=Q>0)
    min_obj = np.sum(Q, where=Q<0)
    penalty = (max_obj-min_obj) * 1.1

    sparseQ = csr_array(Q)
    sparseQ_data = sparseQ.data
    sparseQ_indices = sparseQ.indices
    sparseQ_indptr = sparseQ.indptr
    
    sparseA = csr_array(A)
    sparseA_data = sparseA.data
    sparseA_indices = sparseA.indices
    sparseA_indptr = sparseA.indptr

    @jit
    def matrix_vector_sparse(As_data, As_indices, As_indptr, b):
        res = np.zeros(len(As_indptr)-1, dtype=float)
        for i in range(len(As_indptr)-1):
            for j in range(As_indptr[i], As_indptr[i+1]):
                x = b[As_indices[j]]
                y = As_data[j]
                res[i] += x*y
        return res

    @jit
    def obj_fn_embedding_constraints(x):
        y = matrix_vector_sparse(sparseQ_data, sparseQ_indices, sparseQ_indptr, x)
        z= x @y
        w = np.sum(np.maximum(b - matrix_vector_sparse(sparseA_data, sparseA_indices, sparseA_indptr, x), 0)**2)
        return z + c + penalty * w

    return obj_fn_embedding_constraints

model_to_obj = model_to_obj_sparse_numba


def get_cplex_sol(lp_file: str, obj_fn):
    model: docplex.mp.model.Model = docplex.mp.model_reader.ModelReader.read(lp_file)

    sol: docplex.mp.solution.SolveSolution = model.solve()
    x_cplex = [v.solution_value for v in model.iter_binary_vars()]

    # check consistency with obj_fn
    fx_cplex = obj_fn(np.array(x_cplex, dtype=float))
    assert np.abs(fx_cplex - sol.objective_value) < 1e-8
    
    return x_cplex, fx_cplex


def build_ansatz(ansatz: str, ansatz_params: dict, num_qubits: int, backend: BackendV2) -> tuple[QuantumCircuit, dict | None]:

    def apply_entanglement_map(entanglement):
        # custom-constructed
        if entanglement == 'bilinear':
            return [[i, i+1] for i in range(0, num_qubits-1, 2)] + [[i, i+1] for i in range(1, num_qubits-1, 2)], None

        if entanglement == 'color':
            assert backend.coupling_map.is_symmetric, 'Non-sym coupling map. Do you mean `di-color`?'
            coupling_map = [(i,j) for i,j in backend.coupling_map if i<j]
        elif entanglement == 'di-color':
            coupling_map = list(backend.coupling_map)
            assert not backend.coupling_map.is_symmetric, 'Sym coupling map. Do you mean `color`?'
        if entanglement in ['color', 'di-color']:
            nodes = list(range(backend.num_qubits))
            # TODO: this could be smarter
            for _ in range(num_qubits, backend.num_qubits):
                node_degrees = {n: sum(i == n or j == n for i,j in coupling_map) for n in nodes}
                remove_node = min(node_degrees.keys(), key=(lambda k: node_degrees[k]))
                nodes.remove(remove_node)
                coupling_map = [(i,j) for i,j in coupling_map if i != remove_node and j != remove_node]

            from qiskit_addon_utils.coloring import auto_color_edges
            coloring: dict = auto_color_edges(coupling_map)
            num_colors = max(v for _,v in coloring.items())+1

            out_map = [k for c1 in range(num_colors) for k, c in coloring.items() if c==c1]
            initial_layout = {idx: node for idx, node in enumerate(nodes)}
            reverse_layout = {node: idx for idx, node in enumerate(nodes)}
            return [(reverse_layout[i], reverse_layout[j]) for i,j in out_map], initial_layout
        
        # default
        return entanglement, None

    if ansatz == 'TwoLocal':
        ansatz_params_ = {'rotation_blocks':'ry', 'entanglement_blocks':'cz', 'entanglement': 'bilinear', 'reps': 1}
        ansatz_params_.update(ansatz_params)
        ansatz_params_['entanglement'], initial_layout = apply_entanglement_map(ansatz_params_['entanglement'])
        ansatz_ = TwoLocal(num_qubits, **ansatz_params_)
        ansatz_.measure_all()
    
    elif ansatz == 'bfcd' or 'bfcdR':
        qc_params = ParameterVector(name='p',length=2 if ansatz == 'bfcd' else 1)
        entanglement_block = QuantumCircuit(2)
        # Rzy
        entanglement_block.rx(np.pi / 2, 0)
        entanglement_block.rzz(qc_params[0], 0, 1)
        entanglement_block.rx(- np.pi / 2, 0)
        # Ryz
        entanglement_block.rx(np.pi / 2, 1)
        entanglement_block.rzz(qc_params[1] if ansatz == 'bfcd' else qc_params[0], 0, 1)
        entanglement_block.rx(- np.pi / 2, 1)

        ansatz_params_ = {'rotation_blocks': 'ry',
                          'entanglement_blocks':entanglement_block,
                          'overwrite_block_parameters': True,
                          'flatten': True,
                          'entanglement': 'bilinear',
                          'reps': 1,
                          'skip_final_rotation_layer': True,
                        #   'insert_barriers': True,
                          }
        ansatz_params_.update(ansatz_params)
        if isinstance(ansatz_params_['rotation_blocks'], str):
            ansatz_params_['rotation_blocks'] = get_standard_gate_name_mapping()[ansatz_params_['rotation_blocks']]
        ansatz_params_['entanglement'], initial_layout = apply_entanglement_map(ansatz_params_['entanglement'])
        ansatz_ = NLocal(num_qubits, **ansatz_params_)
        ansatz_.measure_all()

    else:
        raise ValueError('unknown ansatz')
    
    if initial_layout is not None:
        initial_layout = {ansatz_.qubits[k]: v for k,v in initial_layout.items()}
    
    return ansatz_, initial_layout

def get_backend(device: str, instance: str, num_vars: int) -> BackendV2:
    if device == 'AerSimulator':
        aer_options={'method' : 'matrix_product_state', 'n_qubits': num_vars}
        backend = AerSimulator(**aer_options)
    elif device[:4] == 'ibm_':
        service = QiskitRuntimeService()
        backend = service.backend(device, instance)
    else:
        raise ValueError('unknown device')
    
    return backend


def problem_mapping(lp_file: str, ansatz: str, ansatz_params: dict, theta_initial: str, device: str, instance: str):
    model: docplex.mp.model.Model = docplex.mp.model_reader.ModelReader.read(lp_file)

    obj_fn = model_to_obj(model)
    num_vars = model.number_of_binary_variables

    backend = get_backend(device, instance, num_vars)
    if 'from_backend' in ansatz_params:
        build_backend = get_backend(ansatz_params['from_backend'], instance, num_vars)
    else:
        build_backend = backend
    ansatz_params_ = ansatz_params.copy()
    ansatz_params_.pop('from_backend', None)
    ansatz_params_.pop('discard_initial_layout', None)
    ansatz_, initial_layout = build_ansatz(ansatz, ansatz_params_, num_vars, build_backend)
    if ansatz_params.get('discard_initial_layout', False):
        initial_layout = None

    if theta_initial == 'piby3':
        theta_initial_ = np.pi/3 * np.ones(ansatz_.num_parameters)
    else:
        raise ValueError('unknown theta_initial')

    return obj_fn, ansatz_, theta_initial_, backend, initial_layout

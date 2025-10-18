# Solutioning Guide (From Math to Quantum-Hybrid Execution)

This document explains, step by step, how the mathematical formulation of the portfolio problem becomes a runnable quantum-hybrid workflow.

## 1. Mathematical Objective

- The goal is to construct a portfolio whose characteristics match target values as closely as possible.
- A common quadratic form for this optimization problem is: $$\min \sum_{\ell\in L} \sum_{j\in J} \rho_j \big( \sum_{c\in K_\ell} \beta_{c,j} x_c - K^{\text{target}}_{\ell,j} \big)^2$$
- Decision variables $x_c \in \{0,1\}$ represent whether each bond is included in the portfolio or not.
- The quadratic terms encode interactions between bonds, such as correlations and covariances.

## 2. Linear/Quadratic Programming (LP/QP)

- The problem is first expressed in a solver-friendly mathematical form using linear and quadratic programming techniques (e.g., DOcplex LP/QP).
- In this project, an LP file is loaded and converted into a `QuadraticProgram` object for further processing.
- Constraints and penalty methods can embed feasibility into the objective when needed.

## 3. Quadratic Unconstrained Binary Optimization (QUBO)

- The `QuadraticProgram` object is converted to a QUBO: an unconstrained quadratic polynomial over binary variables.
- QUBO is compatible with both sampling-based bitstring evaluations and Ising-type Hamiltonians, both of which are used in variational quantum algorithms (VQAs).

## Optional: Reduced Problem Size

- Since real quantum hardware execution time is limited, the problem dimension is reduced by fixing some variables to 0 and retaining only `NUM_BONDS_TO_KEEP` bonds.
- This approach trades problem realism for computational feasibility within the available quantum resources.

## 4. Quantum Algorithm

- The Variational Quantum Eigensolver (VQE), a type of VQA, is chosen as the quantum algorithm.
- VQE optimizes a parameterized quantum circuit to approximate the minimum eigenvalue of a Hamiltonian, such as the QUBO, making it ideal for solving portfolio optimization problems on current quantum hardware.

## 5. Parameterized Circuit

- An optimal ansatz and hyperparameters are carefully selected:
  - Ansatz type
  - Entanglement pattern
  - Repetitions (`reps`) for circuit depth/expressivity control
  - Rotation blocks
  - Entanglement blocks
- These design choices directly affect the circuit's expressiveness, depth, noise sensitivity, and execution runtime.

## 6. Transpilation

- After the ansatz is built and before any quantum execution (shots, iterations, or epochs), transpilation maps the high-level circuit to the backend's basis gates and coupling map, and applies optimizations.
- If explicit transpilation is skipped, the backend still performs transpilation internally using default settings, which may not be optimal.
- Controlling the optimization level and initial layout can help reduce circuit depth, error rates, and runtime.
- The result is an ISA-ready circuit, often referred to as `isa_ansatz`, that is optimized for the specific quantum hardware target.

## 7. Sampler vs. Estimator

### 7a. Sampler Route (CHOSEN)

1. The parameterized circuit executes to update the ansatz parameter θ.
    - single: One *parameter update* is completed per *iteration*.

2. For a given θ, the sampler measures the circuit and produces bitstrings.
    - single: One *shot* is completed when one *bitstring* (one possible solution) is produced.
    - multiple: Predefined *shots* (`shots`) are completed when many *bitstrings* (many possible solutions) are produced; each bitstring may be unique or duplicated.

3. The objective function value is evaluated using bitstrings.
    - single: The objective function value is evaluated *once* per unique *bitstring*.
    - multiple: The objective function value is evaluated for as *many* unique *bitstrings* as observed (not necessarily `shots`, due to duplicates).

4. Objective function values are sorted in ascending order to form a distribution.
    - single: One *distribution* of objective function values is obtained per *iteration*.

5. CVaR is computed as the average of the lowest tail (the worst α-fraction/the lowest ⌈α·K⌉ values).
    - single: One *function evaluation* is completed per *iteration*.

6. The NFT (Natural Frequency Tuning) optimizer uses this CVaR value/gradient-free update to propose a new θ.
    - single: One *iteration* is completed per *repetition* of one complete cycle (steps 1–6).
    - multiple: Many *iterations* are completed in many *repetitions* of one complete cycle (steps 1–6).

- The quantum-phase search (excluding the local search) requires several such repetitions.
    - single: One *epoch* is completed when many *iterations* are completed.
    - multiple: Predefined *epochs* (`max_epoch`) are completed when many of many *iterations* are completed.

- The above steps are repeated within each epoch.
    - multiple: Many *parameter updates* are completed per *epoch*.
    - multiple: Many *distributions* of objective function values are obtained per *epoch*.
    - multiple: Many *function evaluations* (`step3_fx_evals`) are completed per *epoch*.

**Flow**: QUBO → VQE → parameterized circuit → θ_current → Sampler → bitstring histogram → compute f(b) per bitstring → CVaR → NFT optimizer → optimize θ → θ_new.

### 7b. Estimator Route (NOT CHOSEN)

1. Same as in Sampler.

2. For a given θ, the estimator measures the circuit after applying the Ising Hamiltonian operator (observable) to the current quantum state.
    - single: One *shot* is completed when one *measurement* is made.
    - multiple: Predefined *shots* (`shots`) are completed when many *measurements* are made.

3. The estimator averages these measurements internally to give a single expectation value ⟨H⟩.
    - single: One *expectation value* is computed per *iteration*.

4. The expectation value ⟨H⟩ is used directly as the cost function.
    - single: One *function evaluation* is completed per *iteration*.

5. The optimizer uses this expectation value ⟨H⟩ to propose a new θ.
    - single: One *iteration* is completed per *repetition* of one complete cycle (steps 1–5).
    - multiple: Many *iterations* are completed in many *repetitions* of one complete cycle (steps 1–5).

- The quantum-phase search (excluding the local search) requires several such repetitions.
    - single: One *epoch* is completed when many *iterations* are completed.
    - multiple: Predefined *epochs* (`max_epoch`) are completed when many of many *iterations* are completed.

- The above steps are repeated within each epoch.
    - multiple: Many *parameter updates* are completed per *epoch*.
    - multiple: Many *expectation values* are computed per *epoch*.
    - multiple: Many *function evaluations* are completed per *epoch*.

**Flow**: QUBO → VQE → Ising Hamiltonian H (Pauli operator) → parameterized circuit → θ_current → Estimator → expectation ⟨H⟩ at θ → optimizer → optimize θ → θ_new.

## 8. Classical Local Search

- After the quantum optimization phase completes, classical local search is applied to refine the best quantum solution using bit-flip or coordinate descent methods for several epochs.
- The local search phase complements the quantum exploration by providing fine-grained optimization that can escape local minima that the quantum algorithm might have encountered.

## 9. Results & Analysis

- The complete hybrid optimization results are saved to an experiment file containing all necessary data for analysis, reproducibility, debugging, and research.

***

## Quick Reference

- **QUBO**: objective function over binary variables.
- **Ising Hamiltonian** (H): spin-based Hamiltonian equivalent to QUBO, used in quantum algorithms.
- **Ansatz**: parameterized circuit template used to represent candidate solutions with quantum states |ψ(θ)⟩.
- **Transpilation**: the process of mapping and optimizing a circuit into the hardware-native gates, topology, and connectivity defined by the target device’s Instruction Set Architecture (ISA).
- **ISA-ready circuit**: transpiled circuit compatible with the target device’s Instruction Set Architecture.
- **Bitstring**: one circuit measurement outcome (e.g., `[1,0,1,...,1]`).
- **Sampling**: the process of measuring the circuit multiple times to produce many bitstrings, which together form a distribution over bitstrings.
- **Sampler**: primitive that performs the sampling process.
- **Estimator**: primitive that computes an expectation value by averaging the results from multiple circuit measurements.
- **Observable**: mathematical operator that represents a specific measurable property of a quantum system (e.g., Ising Hamiltonian (H)).
- **Expectation value** (⟨ψ(θ)|H|ψ(θ)⟩): the average measurement result of an observable in a quantum state.
- **Shot**: one circuit measurement.
- **Iteration**: one optimizer step comprising one function evaluation (e.g., one CVaR or one expectation value) and one parameter update; uses multiple shots.
- **Epoch**: a higher-level pass comprising multiple iterations.

$$\text{Total quantum measurements (rough estimate)} = \texttt{shots per iteration} \times \texttt{iterations per epoch} \times \texttt{max epoch}$$

***

## Navigation Guide

### Vanguard Problem Setup

- **Dataset**: `data/1/31bonds/docplex-bin-avgonly-nocplexvars.lp` (31 bonds)
    - **Bond ID Location**: Column D in Excel dataset contains bond IDs
- **Problem**: Portfolio optimization with risk group targeting
    - **Formula**: $$\min \sum_{\ell\in L} \sum_{j\in J} \rho_j \big( \sum_{c\in K_\ell} \beta_{c,j} x_c - K^{\text{target}}_{\ell,j} \big)^2$$
    - **Bonds**: Each bond `c` is held in the portfolio at amount `x_c ∈ {0,1}` (binary decision)
    - **Risk Groups**: Each bond `c` belongs to at least one risk group (category) `l`
    - **Characteristics**: Each characteristic `j` is a fixed property of a bond that influences the outcome
    - **Targets**: Each risk group `l` has specific target values for all characteristics
    - **Objective**: Specify `x_c` in the portfolio to match each risk group's characteristics to target values
    - **Constraints**: Portfolio capacity is specified manually

### Vanguard Source Code Organization

```
root/src/
├── experiment.py: Data management, dataclasses, result storage, loading, etc.
├── plots.py: Visualization and analysis
├── runner.py: Wrapper class for serverless execution
├── serverless_runner.py: Serverless execution entry point
├── step_1.py: Problem conversion (LP to quantum) and quantum circuit setup
└── sbo/
    ├── constants.py: Configuration constants
    ├── version.py: Version information
    ├── _converters/: Quantum-ready problem transformations (general format → QUBO format)
    ├── _problems/: Problem definitions and constraints (math → CS)
    ├── _translators/: Format interoperability layer (Docplex/Ising ↔ quadratic)
    ├── optimizer/: Optimization algorithms and monitoring
    ├── patterns/: Building blocks for optimization workflows
    │   ├── building_blocks/: The actual workflow steps
    │   └── functions/: Optimization function
    └── utils/: Utility functions
```

### Vanguard Experimental Parameters

- **Ansatz Types**: TwoLocal, BFCD, BFCD-R
- **Entanglements**: Full, Bilinear, Color
- **Repetitions**: 1, 2, 3 reps
- **Problem Sizes**: 31, 109, 155 qubits
- **Devices**: AerSimulator, IBM Kyiv, IBM Marrakesh, IBM Fez
- **Alpha Values**: 0.1, 0.15, 0.2

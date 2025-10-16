# Project 2: Quantum for Portfolio Optimization

## 📝 About This Repository

This repository is a **remake** of the original project, independently developed by me as part of my continuous learning and improvement efforts. While this version includes significant modifications, enhancements, and reanalysis, the original project was a collaborative team effort, with *Aung Phone Kyaw* contributing alongside me.

**Credits**:
- **Remake Project**: Developed by *La Wun Nannda*
- **Original Project**: Developed by the *NaiveQuantum* team
- **Original Project Repository**: [click here](https://github.com/lawun330/WISER_Optimization_VG/)

This remake represents my own work and contributions while honoring the collaborative foundation of the original project.

## 👥 Team

Name: **NaiveQuantum**

Members:
| Name | WISER Enrollment ID |
|------|-------------------|
| La Wun Nannda | gst-9Znx386rMl8rJMQ |
| Aung Phone Kyaw | gst-lXnHQNnvqFrUrS6 |

## 📋 Project Summary

This project implements a comprehensive comparative study of quantum computing techniques for portfolio optimization, specifically addressing the task of selecting optimal bond portfolios from a universe of 31 fixed income securities. We employ Variational Quantum Algorithms (VQAs) with the Variational Quantum Eigensolver (VQE) and Conditional Value-at-Risk (CVaR) optimization to solve this complex financial optimization problem.

The core challenge involves minimizing the difference between a portfolio's characteristics and target values while satisfying various constraints. Traditional classical optimization methods face computational challenges as problem size scales, making quantum computing an attractive alternative through its inherent ability to explore large solution spaces efficiently using quantum superposition and entanglement.

## 🔬 Research Focus

Our comparative analysis aims to identify the best quantum optimization strategy based on the following research questions:

1. **"Quantum vs. Hybrid"**: Does classical post-processing help reach target quality faster?
2. **"Lightweight Deep vs. Heavyweight Shallow"**: Does parameter efficiency or circuit depth matter for solution quality?
3. **Speed to Target Quality**: Which configuration reaches the standardized solution quality fastest?
4. **Other Factors**: What additional factors are likely to affect the performance of each approach?
5. **Computational Efficiency**: Which approach minimizes computational cost while maintaining throughput?

## ⚡ Four Approaches

To answer these questions, we designed four distinct quantum configurations that systematically vary key algorithmic parameters:

1. **Lightweight Quantum**: BFCD ansatz with bilinear entanglement (high reps)
2. **Lightweight Hybrid**: BFCD ansatz with bilinear entanglement + Local Search (high reps)
3. **Heavyweight Quantum**: TwoLocal ansatz with full entanglement (low reps)
4. **Heavyweight Hybrid**: TwoLocal ansatz with full entanglement + Local Search (low reps)

## ⚙️ Technical Implementations

Our approach uses a QUBO (Quadratic Unconstrained Binary Optimization) formulation that transforms the original linear programming (LP) problem into a format suitable for VQAs. The conversion process involves constraint handling and objective function reformulation to ensure effective quantum algorithm exploration.

### 1. Lightweight Quantum
- **Ansatz**: BFCD ansatz with bilinear entanglement
- **Rationale**: BFCD ansatz uses specialized RZZ gates with optimized rotation patterns, making it inherently more parameter-efficient. Bilinear entanglement provides structured connectivity while minimizing gate count.
- **Parameters**: High reps (3) for deep circuit exploration

### 2. Lightweight Hybrid
- **Ansatz**: BFCD ansatz with bilinear entanglement + Local Search post-processing
- **Rationale**: Combines BFCD's parameter efficiency with classical local search refinement
- **Parameters**: High reps (3) + Local Search optimization

### 3. Heavyweight Quantum
- **Ansatz**: TwoLocal ansatz with full entanglement
- **Rationale**: TwoLocal ansatz uses standard rotation gates with more parameters but shallower circuits. Full entanglement captures maximum correlations between bonds.
- **Parameters**: Low reps (2) to balance resource usage

### 4. Heavyweight Hybrid
- **Ansatz**: TwoLocal ansatz with full entanglement + Local Search post-processing
- **Rationale**: Combines full entanglement's correlation capture with classical optimization
- **Parameters**: Low reps (2) + Local Search optimization

## 🔍 Role of Local Search
Local Search is a post-processing technique that performs classical optimization on the quantum solution, potentially helping reach target quality faster by:
- **Bit-flip optimization**: Systematically testing single-bit changes
- **Local neighborhood search**: Exploring nearby solutions
- **Classical refinement**: Using classical methods to polish quantum results

***

## 📁 Project Structure

```
root/
├── 📊 data/                        # Problem datasets (Vanguard)
└── 📁 misc/                        # Miscellaneous files (Vanguard)
├── 📋 project/                     # Main project directory (NaiveQuantum)
├── 🔧 src/                         # Source code (Vanguard)
│   └── 🏗️ sbo/                     # Sampling-Based Optimization framework (Vanguard)
```

## 🛠️ Technologies Used

- **Quantum Framework**: Qiskit
- **Optimization**: VQE
- **Risk Measure**: CVaR
- **Backend**: AerSimulator
    - GPU acceleration is not feasible for this project due to current Qiskit AerSimulator limitations. According to the [official Qiskit documentation](https://qiskit.github.io/qiskit-aer/stubs/qiskit_aer.AerSimulator.html), the `matrix_product_state` method (required for 31-qubit problems) does not support GPU.
- **Problem Formulation**: QUBO transformation
- **Post-processing**: Local Search optimization

## 🚀 Setup

1. Clone the repository
2. Create virtual environment
```console
conda env create -f conda_environment.yaml
```
or
```console
python -m venv VQE_vanguard_womanium_wiser_2025
pip install -r requirements.txt
```
3. Activate the environment
```console
conda activate VQE_vanguard_womanium_wiser_2025
```
or
```console
.\VQE_vanguard_womanium_wiser_2025\Scripts\activate
```

***

## 📊 Experimental Results

- **Solution Quality**: All approaches achieved similar relative gaps (~56.5%) from the optimal classical solution
- **Hybrid Approaches**: Local search post-processing showed no improvement (0% hybrid improvement)
- **Execution Time**: Ranged from 24.7 minutes (Heavyweight Hybrid) to 195.1 minutes (Lightweight Quantum)
- **Computational Cost**: Function evaluations ranged from 1,862 (Heavyweight Hybrid) to 8,191 (Lightweight Quantum)

## 🎯 Conclusions

The **heavyweight hybrid** configuration emerged as the optimal choice.

1. **Speed**: Achieved target quality in 24.7 minutes (5.3× faster than lightweight quantum)
2. **Cost**: Best efficiency score (7.17×10⁻⁴) balancing quality and speed

**Key Insight**: While hybrid post-processing doesn't improve solution quality, the heavyweight configuration's shallow circuit design (reps=2) with full entanglement achieves optimal performance through reduced computational overhead.

## 🚀 Future Work

We are hopeful about the future prospects of quantum portfolio optimization, particularly with the recent advances in quantum hardware architecture. Full entanglement is motivated by recent advances in quantum hardware architecture such as tunable couplers in the Ankaa architecture (Mutus, 2025). This advancement eases the implementation of fully entangled circuits, such as the two-local full entanglement ansatz, making them more practical on real quantum hardware.

Our ultimate goal is to deploy these four configurations on real IBM quantum hardware to validate their performance in a noisy quantum environment. This real-world testing will provide crucial insights into the practical viability of quantum portfolio optimization and help identify which approach is most robust against quantum noise and hardware limitations.

***

## References

- Barkoutsos, P. K., Nannicini, G., Robert, A., Tavernelli, I., & Woerner, S. (2020, April 20). Improving variational quantum optimization using CVaR. *Quantum*, 4, 256. [click here](https://quantum-journal.org/papers/q-2020-04-20-256/?utm_source=researcher_app&utm_medium=referral&utm_campaign=RESR_MRKT_Researcher_inbound#)

- Chen, C. (2020, October 8). Portfolio optimization with Variational Quantum Eigensolver (VQE)-(2). *Medium*. [click here](https://eric08000800.medium.com/portfolio-optimization-with-variational-quantum-eigensolver-vqe-2-477a0ee4e988)

- Mehta, B. (2025, June 18). *2025 QUANTUM PROGRAM ❯ Day 7 ❯ Projects Orientation Part 2* [Video]. YouTube. [click here](https://youtu.be/YF9bOORmHy4)

- Mutus, J. (2025, July 17). *Quantum hardware demystified ❯ Dr. Josh Mutus ❯ 2025 QUANTUM PROGRAM* [Video]. YouTube. [click here](https://youtu.be/EIL2MEvyGp8)

## License

Some code and data in this repository are proprietary materials from Vanguard and remain their intellectual property. These materials are provided for educational purposes only and may not be redistributed, modified, or used for commercial purposes without explicit permission from Vanguard.

# 1. Challenge Overview:
Vanguard’s portfolio construction process lies at the heart of its investment strategy, balancing risk, return, and investor preferences across a vast landscape of asset classes and constraints. However, as portfolios grow in complexity—spanning thousands of securities, intricate guardrails, and real-time trading demands—classical optimization tools like GUROBI face growing limitations in speed, scalability, and solution diversity. This challenge explores how sampling-based quantum optimization can be harnessed to overcome these barriers. By leveraging hybrid quantum-classical algorithms and decomposition pipelines, the goal is to prototype a quantum-enhanced solution that can:

1. 	Efficiently solve high-dimensional, constraint-heavy portfolio optimization problems.
2. 	Deliver near-optimal asset allocations within tight runtime windows.
3. 	Scale to real-world use cases like fixed income ETF creation and index tracking.
4. Preserve critical business metrics such as tracking error, excess return, and risk exposure.

The project focuses on using binary decision variables and quadratic objectives to simulate realistic trading scenarios. The challenge lies not only in achieving computational gains but also in maintaining interpretability, robustness, and alignment with investment principles. 


# 2. Challenge Duration:
 * 4 weeks
 * Teams start working on July 15, 2025
 * Teams submit their challenge solutions on August 10, 2025

# 3. Team Guidelines:
*	Team size - Maximum 3 participants per team.
*	All team participants must be enrolled in Womanium WISER Quantum 2025.
*	Everyone is eligible to participate in this challenge and win Womanium grants.
*	Best participants get selected for Womanium QSL fellowships with Vanguard.

# 4. Challenge Tasks/ Deliverables:
The participants are expected to complete for eligible challenge submission:

1)	Review the mathematical formulation provided below, focusing on binary decision variables, linear constraints, and the quadratic objective.
2)	(necessary to pass the project) Convert the binary optimization problem to a formulation that is compatible with a quantum optimization algorithm. For example, convert the constrained problem to an unconstrained problem.
3)	(necessary to pass the project) Write a quantum optimization program for handling problems of the type in (2). An example of such an optimization routine which is used in portfolio optimization is the Variational Quantum Eigensolver (see resources below), however you may pursue what you judge to be the best solution.
4)	(challenge) Solve the optimization problem in (1) using your quantum formulation.
5)	(challenge subtask) Validate your solution in (4) using a classical optimization routine. Compare the solution quality against the benchmark classical solution in terms of the cost function, and include relevant performance metrics(e.g., convergence of the optimization routine, and scaling properties with problem size).
 
Note: No formal presentation is required. Instead, we’ll host a “show-and-tell” style session where each team will walk through their approach and demonstrate their prototype live. This is your opportunity to showcase your thinking, creativity, and results in an informal, interactive format.

# 5. Quantum Hardware Credits / Platform:
*	Participants may use any quantum SDK or platform of their choice.

# 6. Judging Criteria:
Solutions will be evaluated against internal benchmark implementations at Vanguard. Evaluation will be based on:
*	Speed of the solution
*	Optimality (as measured by the cost function)
*	Scalability (problem size handled)

# 7. Resources:

*	An example of how VQE can be implemented - https://eric08000800.medium.com/portfolio-optimization-with-variational-quantum-eigensolver-vqe-2-477a0ee4e988
*	A useful paper on variational Quantum Optimization https://quantum-journal.org/papers/q-2020-04-20-256/?utm_source=researcher_app&utm_medium=referral&utm_campaign=RESR_MRKT_Researcher_inbound
*	Video recording for project orientation 2025 QUANTUM PROGRAM ❯ Day 7 ❯ Projects Orientation Part 2 - YouTube

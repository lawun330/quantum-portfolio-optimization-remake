# Copyright (C) 2024-2025 IBM Quantum
#
# This code is categorized as "existing" IBM asset
# as a part of Quantum Acceleration contract.
"""
Utility methods for using lp files.
"""
import os
from datetime import datetime

from .._problems import QuadraticProgram
from .lp_parser import LPParser


def read_lp_file(lp_file_path):
    """
    Read an lp file and parse it into an LPParser object.

    Parameters:
        lp_file_path (str): The path to the lp file to be parsed.

    Returns:
        LPModel: An LPModel object representing the parsed lp file.
    """
    parser = LPParser(lp_file_path)
    parser.parse()
    return parser


def load_quadratic_program(lp_file_path):
    """
    Create a QuadraticProgram from an LP file.

    Args:
        lp_file_path (str): The path to the LP file.

    Returns:
        QuadraticProgram: The loaded QuadraticProgram.
    """
    parser = read_lp_file(lp_file_path)

    qp = QuadraticProgram()

    all_vars = set(parser.objective)
    all_vars.update(var for pair in parser.quadratic_objective for var in pair)

    for var in all_vars:
        # Here we assume all variables are binary. Adjust as needed.
        qp.binary_var(name=var)

    linear_objective = dict(parser.objective)

    quadratic_objective = {
        (var1, var2): coef for (var1, var2), coef in parser.quadratic_objective.items()
    }

    qp.minimize(linear=linear_objective, quadratic=quadratic_objective)

    for var, (lb, ub) in parser.bounds.items():
        if var in qp.variables:
            qp.variables[var].set_bounds(lb, ub)

    return qp


def load_quadratic_program_from_lp_str(problem_str: str):
    """
    Create a QuadraticProgram from an LP string using local parser

    Parameters:
        problem_str: The content of the LP file.

    Returns:
        QuadraticProgram: The QuadraticProgram.
    """
    current_timestamp = datetime.now()
    filename = f"{current_timestamp}.lp"
    with open(filename, "w", encoding="utf-8") as file:
        file.write(problem_str)

    # model = ModelReader.read(filename, ignore_names=True)
    try:
        problem = load_quadratic_program(filename)
    finally:
        os.remove(filename)
    return problem


def load_quadratic_program_from_lp_str_cplex(problem_str: str):
    """
    Create a QuadraticProgram from an LP string using cplex (if installed)

    Parameters:
        problem_str: The content of the LP file.

    Returns:
        QuadraticProgram: The QuadraticProgram.
    """
    current_timestamp = datetime.now()
    filename = f"{current_timestamp}.lp"
    with open(filename, "w", encoding="utf-8") as file:
        file.write(problem_str)

    # model = ModelReader.read(filename, ignore_names=True)
    try:
        problem = QuadraticProgram()
        problem.read_from_lp_file(filename)
    finally:
        os.remove(filename)

    return problem

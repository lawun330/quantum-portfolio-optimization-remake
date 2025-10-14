# Copyright (C) 2024-2025 IBM Quantum
#
# This code is categorized as "existing" IBM asset
# as a part of Quantum Acceleration contract.
"""Experimental parser for LP files."""
import re


class LPParser:
    """
    Experimental parser for LP files. This is used to skip cplex when creating Quadratic Programs.
    Not all features of LP files are implemented!

    """

    def __init__(self, filename):
        """Initialize an LPParser object.

        Args:
            filename (str): Path to the LP file.
        """
        self.filename = filename
        self.objective = {}
        self.quadratic_objective = {}
        self.bounds = {}
        self.binaries = []

    def parse(self):
        """
        Parse the optimization problem from a file.

        Parameters:
        - filename (str): The name of the file to parse.

        Returns:
        - None
        """
        with open(self.filename, "r", encoding="utf-8") as file:
            section = None
            objective_lines = []
            for line in file:
                line = line.strip()
                # Skip empty lines
                if not line:
                    continue

                if line.lower().startswith("minimize") or line.lower().startswith("maximize"):
                    section = "objective"
                    continue
                if line.lower().startswith("subject to"):
                    section = "constraints"
                    continue
                if line.lower().startswith("bounds"):
                    section = "bounds"
                    continue
                if line.lower().startswith("binar"):
                    section = "binary"
                    continue
                if line.lower().startswith("end"):
                    section = None
                    continue

                if section == "objective":
                    # Gather all lines
                    objective_lines.append(line)
                if section == "bounds":
                    self._parse_bounds(line)
                if section == "binary":
                    self._parse_binary(line)

            if objective_lines:
                full_objective = " ".join(objective_lines)
                self._parse_objective(full_objective)

    def _parse_objective(self, line):
        # Handle quadratic terms in brackets like [ ... ]/2
        bracketed_expression = re.findall(r"\[(.*?)\]\s*/\s*(\d+)", line)
        for expr, divisor in bracketed_expression:
            linear_terms = re.findall(r"([+-]?\s*\d*\.?\d+|\d+)\s+(\w+)(?=\s|$)", expr)
            self._parse_liniar_terms(linear_terms, float(divisor))
            reg = r"([+-]?\s*(?:\d+(?:\.\d+)?|\.\d+))\s+([a-zA-Z_]\w*)\s*(?:\*\s*([a-zA-Z_]\w*)|\^\s*2)"
            quadratic_terms = re.findall(reg, expr)
            self._parse_quadratic_terms(quadratic_terms, float(divisor))

            line = line.replace(f"[{expr}]/" + str(divisor), "")

        # terms outside of brackets
        self._parse_remaining_terms(line)

    def _parse_liniar_terms(self, linear_terms, divisor=1.0):
        for coef, var in linear_terms:
            coef = coef.strip().replace(" ", "")
            if coef in ("+", "-"):
                coef += "1"
            coef = float(coef) / divisor
            self.objective[var] = coef

    def _parse_quadratic_terms(self, quadratic_terms, divisor=1.0):
        for coef, var1, var2 in quadratic_terms:
            coef = coef.strip().replace(" ", "")
            if coef in ("+", "-"):
                coef += "1"
            coef = float(coef) / divisor
            if not var2:  # Handle squared terms like x1^2
                var2 = var1
            self.quadratic_objective[(var1, var2)] = coef

    def _parse_remaining_terms(self, line):
        linear_terms = re.findall(r"([+-]?\s*\d*\.?\d+|\d+)\s+(\w+)(?=\s|$)", line)
        self._parse_liniar_terms(linear_terms)

        quadratic_terms = re.findall(
            r"([+-]?\s*\d*\.?\d+|\d+)\s+(\w+)\s*(?:\*\s*(\w+)|\^\s*2)", line
        )
        self._parse_quadratic_terms(quadratic_terms)

    def _parse_bounds(self, line):
        # Example input "1.5 <= x <= 3.0"
        reg = r"^\s*(\d+(?:\.\d+)?|\.\d+)\s*<=\s*([a-zA-Z_]\w*)\s*<=\s*(\d+(?:\.\d+)?|\.\d+)\s*$"
        match = re.match(reg, line)
        if match:
            lower, var, upper = match.groups()
            self.bounds[var] = (float(lower), float(upper))
        # else - only binary variables for now

    def _parse_binary(self, line):
        binaries = line.split()
        self.binaries.extend(binaries)

    def get_objective(self):
        """
        Returns the objective of the optimization problem.

        Args:
            None

        Returns:
            str: The objective of the optimization problem.
        """
        return self.objective

    def get_quadratic_objective(self):
        """
        Returns the quadratic objective of the optimization problem.

        Args:
            None

        Returns:
            The quadratic objective as a numpy array.
        """
        return self.quadratic_objective

    def get_bounds(self):
        """
        Returns the bounds of the parameters.

        Parameters:
        - None

        Returns:
        - bounds (list of tuples): A list of tuples representing the lower and
        upper bounds for each parameter.
        """
        return self.bounds

    def get_binaries(self):
        """
        Returns a list of binary parameters.

        Parameters:
        - self (object): The current object instance.

        Returns:
        - binaries (list): A list of binary file parameters.
        """
        return self.binaries

# This code is part of a Qiskit project.
#
# (C) Copyright IBM 2019, 2023.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

"""
Optimization converters (:mod:`_converters`)
===============================================================

.. currentmodule:: _converters

This is a set of converters having `convert` functionality to go between different representations
of a given :class:`~_problems.QuadraticProgram` and to `interpret` a given
result for the problem, based on the original problem before conversion, to return an appropriate
:class:`~_.algorithms.OptimizationResult`.

Base class for converters
-------------------------

.. autosummary::
   :toctree: ../stubs/
   :nosignatures:

   QuadraticProgramConverter

Converters
----------

.. autosummary::
   :toctree: ../stubs/
   :nosignatures:

   InequalityToEquality
   IntegerToBinary
   LinearEqualityToPenalty
   LinearInequalityToPenalty
   MaximizeToMinimize
   MinimizeToMaximize
   QuadraticProgramToQubo

"""

from .flip_problem_sense import MaximizeToMinimize, MinimizeToMaximize
from .inequality_to_equality import InequalityToEquality
from .integer_to_binary import IntegerToBinary
from .linear_equality_to_penalty import LinearEqualityToPenalty
from .linear_inequality_to_penalty import LinearInequalityToPenalty
from .quadratic_program_converter import QuadraticProgramConverter
from .quadratic_program_to_qubo import QuadraticProgramToQubo

__all__ = [
    "InequalityToEquality",
    "IntegerToBinary",
    "LinearEqualityToPenalty",
    "LinearInequalityToPenalty",
    "MaximizeToMinimize",
    "MinimizeToMaximize",
    "QuadraticProgramConverter",
    "QuadraticProgramToQubo",
]

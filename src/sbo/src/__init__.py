# Copyright (C) 2024 IBM Quantum
#
# This code is categorized as "existing" IBM asset
# as a part of Quantum Acceleration contract.

"""
Sampling Based Optimization Function module (:mod:`src`)
===============================================================
.. currentmodule:: src


"""
import logging

from .constants import LOG_FILE
from .version import __version__


def _setup_logger(logger: logging.Logger) -> None:
    """Setup the logger for the circuit function modules."""
    log_fmt = "%(asctime)s %(levelname)s %(module)s: %(message)s"
    formatter = logging.Formatter(log_fmt)

    # Set propagate to `False` since handlers are to be attached.
    logger.propagate = False

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    logger.setLevel(logging.DEBUG)
    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)


_setup_logger(logging.getLogger(__name__))

__all__ = ["__version__"]

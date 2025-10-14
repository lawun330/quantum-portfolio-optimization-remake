# Copyright (C) 2025 IBM Quantum
#
# This code is categorized as "existing" IBM asset
# as a part of Quantum Acceleration contract.
"""Utilities"""
import logging
from typing import Any

LOGGER = logging.getLogger(__name__)


def get_value(dictionary: dict, key: str, default: Any, error: bool = False):
    """
    Utility function that returns the default value if the key is not present or the value is None.
    If error=True, raises an exception instead of using the default.

    Args:
        dictionary: dictionary with keys and values
        key: key to be searched
        default: default value
        error: if True, key must be present with a not None value
    """
    value = dictionary.get(key, None)

    if value is None:
        if error:
            raise KeyError(f"The key '{key}' must be present in the dictionary and cannot be None.")
        LOGGER.warning("Using default value for key '%s': %s", key, str(default))
        return default

    return value

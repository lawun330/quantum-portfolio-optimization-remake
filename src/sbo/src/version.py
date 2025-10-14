# Copyright (C) 2024 IBM Quantum
#
# This code is categorized as "existing" IBM asset
# as a part of Quantum Acceleration contract.

"""Versioning for the Library."""

VERSION = "0.1.0"


def get_version_info() -> str:
    """
    Get the full version string.

    Returns:
        The version string, e.g. '0.1.0'

    """
    return VERSION


__version__ = get_version_info()

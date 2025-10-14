# Copyright (C) 2024-2025 IBM Quantum
#
# This code is categorized as "existing" IBM asset
# as a part of Quantum Acceleration contract.
"""
Minimization methods with quantum. NFT
"""
from __future__ import annotations

import logging
from itertools import combinations
from typing import Callable

import numpy as np

from numba import jit

LOGGER = logging.getLogger(__name__)

@jit
def _core(x, val, refval, maxfevals, all_combinations, maxiter, func, maxepoch):
    fevals = 0
    epoch = 0
    is_local_minimum = True

    while True:  # "while x not local minimum"

        if np.isclose(val, refval) or val < refval:
            break
        if maxfevals != -1 and fevals >= maxfevals:
            break

        combs = np.random.permutation(all_combinations)
        if maxiter is not None:
            # maxiter is not present in the paper
            combs = combs[:maxiter]

        is_local_minimum = True
        for comb in combs:
            z = np.copy(x)
            for idx in comb:
                z[idx] = 1 - z[idx]

            val_flip = func(z)
            fevals += 1
            if maxfevals != -1 and fevals >= maxfevals:
                is_local_minimum = False
                break

            if val_flip < val:
                x = z
                val = val_flip
                is_local_minimum = False
                break

        if is_local_minimum and maxiter is None:
            break
        if maxepoch != -1 and epoch >= maxepoch:
            break
        epoch += 1
    
    return x, val, epoch, fevals, is_local_minimum

def _local_search_general(x, val, func: Callable, options):
    """
    Reference paper: https://arxiv.org/pdf/2406.01743 (q-ctrl)
    Args:
    x: initial bitstring
    val: func(x) - to avoid recalculating
    func: objective function
    **options (dict): Additional keyword arguments passed to the objective function.
            "local_search_num_bitflips" - biflips allowed to define a new test point.
             Default 1.
            "local_search_maxiter" (int | None) - maximal number of bitflips tested from point x.
            If None, no limit is applied. Default None.
            "local_search_maxepoch" (int | None) - after a better x is selected, the entire procedure is repeated,
                but no more than `maxepoch` times. If None, no limit is applied.  Default 5.
            "local_search_maxfevals" (int | None) - stops local search after that many fevals.
            If None, no limit is applied.  Default None.
            "refval" (float | None) - If hit, the local search is aborted. If None, not tested.
    """
    # this fn corresponds to the pseudocode of GreedyPass() in Algorithm 1 of the paper
    k = options.get("local_search_num_bitflips", 1)
    maxiter = options.get("local_search_maxiter", None)
    maxepoch = options.get("local_search_maxepoch", 5)
    refval = options.get("refval", None)
    maxfevals = options.get("local_search_maxfevals", None)

    if maxfevals is None:
        maxfevals = -1
    if maxepoch is None:
        maxepoch = -1

    n = len(x)

    all_combinations = np.array(list(combinations(range(n), k)))

    return _core(x.astype(float), val, refval, maxfevals, all_combinations, maxiter, func, maxepoch)

def repeated_local_search_general(x, val, func: Callable, options):
    """
    Repeats the local search `maxreps` times
    Reference paper: https://arxiv.org/pdf/2406.01743 (q-ctrl)
    Args:
    x: initial bitstring
    val: func(x) - to avoid recalculating
    func: objective function
    **options (dict): Additional keyword arguments passed to the objective function.
            "local_search_num_bitflips" - biflips allowed to define a new test point.
            Default 1.
            "local_search_maxiter" (int | None) - maximal number of bitflips tested from point x.
            If None, no limit is applied. Default None.
            "local_search_maxepoch" (int | None) - after a better x is selected, the entire procedure is repeated,
                but no more than `maxepoch` times. If None, no limit is applied.  Default 5.
            "local_search_maxfevals" (int | None) - stops local search after that many fevals (per rep).
                If None, no limit is applied.  Default None.
            "local_search_repeated_maxreps" - maximum repetitions of the local search (since the
                local search is randomized, it is repeated multiple times with a different
                sorting in the exploration tree). Default 1
            "refval" (float) - if hit, the local search is aborted
    """
    maxreps = options.get("local_search_repeated_maxreps", 1)
    refval = options.get("refval", None)
    x_best = x
    val_best = val

    num_epochs = []
    num_fevals = []
    vals = []

    for _ in range(maxreps):  # loop over k in the pseudocode of Algorithm 2 "LocalSolver"
        x_new, val_new, epochs, fevals, is_local_minimum = _local_search_general(
            x, val, func, options
        )

        if np.isclose(val_best, np.float64(refval)) or val_best < refval:
            break

        num_epochs.append(epochs)
        num_fevals.append(fevals)
        vals.append(val_new)

        if val_new < val_best:
            x_best = x_new
            val_best = val_new

        if epochs == 0 and is_local_minimum:
            break

    # LOGGER.info(
    #     "Repeated local search - %s->%s (%.2f%%), epochs %s, fevals %s, vals %s",
    #     val,
    #     val_best,
    #     val_best / val * 100,
    #     num_epochs,
    #     num_fevals,
    #     vals,
    # )

    return x_best, val_best, num_epochs, num_fevals, vals

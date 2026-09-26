"""The two circularity reveal tests and the statistics they share."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .matrix import ScoreMatrix


def critical_difference(matrix: ScoreMatrix, alpha: float = 0.05,
                        n_perm: int = 10_000, seed: int = 42) -> float:
    """Randomized Tukey HSD critical difference on a complete system-by-topic
    block. Within each topic the system labels are permuted, which destroys any
    true ordering while keeping topic difficulty intact; over ``n_perm``
    permutations the range of the system means forms a null distribution. The
    returned ``(1 - alpha)`` quantile is the gap between two systems' mean
    scores that chance exceeds only ``alpha`` of the time."""
    vals = matrix.values
    rng = np.random.default_rng(seed)
    max_range = np.empty(n_perm)
    chunk = 500
    for start in range(0, n_perm, chunk):
        n = min(chunk, n_perm - start)
        perm = rng.permuted(np.broadcast_to(vals, (n,) + vals.shape), axis=1)
        means = perm.mean(axis=2)  # n x systems
        max_range[start:start + n] = means.max(axis=1) - means.min(axis=1)
    return float(np.quantile(max_range, 1 - alpha))


def theil_sen(x, y) -> tuple[float, float]:
    """Robust affine fit ``y = a + b*x``: the slope ``b`` is the median of the
    slopes through all pairs of points and the intercept ``a`` the median of
    ``y - b*x``. Its breakdown point near 29 percent lets a minority of circular
    systems sit off the line without steering it. Returns ``(a, b)``."""
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    i, j = np.triu_indices(len(x), k=1)
    dx = x[j] - x[i]
    ok = dx != 0
    b = float(np.median((y[j] - y[i])[ok] / dx[ok]))
    a = float(np.median(y - b * x))
    return a, b


def _require_aligned(tested: ScoreMatrix, reference: ScoreMatrix) -> None:
    if tested.systems != reference.systems or tested.topics != reference.topics:
        raise ValueError(
            "tested and reference matrices must share systems and topics; "
            "build them with circularity_reveal.align()")


@dataclass(frozen=True)
class SwapResult:
    """Outcome of the swap test."""

    revealed: frozenset[str]
    unconfirmed: dict[str, int]
    contradicted: dict[str, int]
    d_tested: float
    d_reference: float
    theta: float


def swap_test(tested: ScoreMatrix, reference: ScoreMatrix, alpha: float = 0.05,
              theta_frac: float = 0.20, n_perm: int = 10_000,
              seed: int = 42) -> SwapResult:
    """Reveal systems whose certified wins under the tested nugget bank are not
    upheld by the reference. For every pair where ``s`` beats ``j`` by more than
    the tested critical difference, the reference either contradicts the win, by
    certifying ``j`` over ``s``, or leaves it unconfirmed, a tie within the
    reference critical difference. A system is revealed on one contradicted win,
    or on more unconfirmed wins than ``theta_frac`` of all systems. The test
    assumes nothing about how the two score scales relate, so it needs a diverse
    pool of comparison systems."""
    _require_aligned(tested, reference)
    d_b = critical_difference(tested, alpha, n_perm, seed)
    d_r = critical_difference(reference, alpha, n_perm, seed)
    mb = tested.values.mean(axis=1)
    mr = reference.values.mean(axis=1)
    theta = theta_frac * len(tested.systems)
    unconfirmed: dict[str, int] = {}
    contradicted: dict[str, int] = {}
    revealed = set()
    for i, s in enumerate(tested.systems):
        u = c = 0
        for j in range(len(tested.systems)):
            if j == i or not (mb[i] - mb[j] > d_b):
                continue
            if not (mr[i] - mr[j] > d_r):
                u += 1
            if mr[j] - mr[i] > d_r:
                c += 1
        unconfirmed[s], contradicted[s] = u, c
        if c >= 1 or u > theta:
            revealed.add(s)
    return SwapResult(frozenset(revealed), unconfirmed, contradicted,
                      d_b, d_r, theta)


@dataclass(frozen=True)
class ValueResult:
    """Outcome of the value test."""

    revealed: frozenset[str]
    intercept: float
    slope: float
    d_residual: float
    residual: dict[str, float]


def value_test(tested: ScoreMatrix, reference: ScoreMatrix, alpha: float = 0.05,
               n_perm: int = 10_000, seed: int = 42) -> ValueResult:
    """Reveal systems that score higher under the tested nugget bank than a
    robust affine fit from the reference predicts. The fit
    ``tested = a + b * reference`` comes from Theil-Sen regression on the system
    means, and the per-topic residual matrix feeds the same permutation test for
    a residual critical difference ``d_residual``. A system is revealed when its
    mean residual exceeds ``d_residual``, one-sided for inflation only. The test
    assumes the two nugget banks are affinely related, and it catches inflation
    at any rank, including the top."""
    _require_aligned(tested, reference)
    mb = tested.values.mean(axis=1)
    mr = reference.values.mean(axis=1)
    a, b = theil_sen(mr, mb)
    residual_matrix = ScoreMatrix(tested.systems, tested.topics,
                                  tested.values - (a + b * reference.values))
    d_e = critical_difference(residual_matrix, alpha, n_perm, seed)
    residual = {s: float(mb[i] - (a + b * mr[i]))
                for i, s in enumerate(tested.systems)}
    revealed = frozenset(s for s, r in residual.items() if r > d_e)
    return ValueResult(revealed, a, b, d_e, residual)

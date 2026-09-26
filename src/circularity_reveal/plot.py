"""Result plot for the two reveal tests (requires matplotlib)."""
from __future__ import annotations

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle

from .matrix import ScoreMatrix
from .reveal import SwapResult, ValueResult

_FILL = (("both", "crimson", "revealed by both tests"),
         ("swap", "lightskyblue", "revealed by swap test only"),
         ("value", "gold", "revealed by value test only"))


def _legend(ax, planted, potential) -> None:
    handles = [Line2D([0], [0], marker="o", ls="", markerfacecolor="none",
                      markeredgecolor="black", markeredgewidth=0.7,
                      markersize=6, label="system")]
    for _, color, label in _FILL:
        handles.append(Line2D([0], [0], marker="o", ls="",
                              markerfacecolor=color, markeredgecolor="black",
                              markeredgewidth=0.7, markersize=6, alpha=0.85,
                              label=label))
    if planted:
        handles.append(Line2D([0], [0], marker="*", ls="",
                              markerfacecolor="none", markeredgecolor="black",
                              markeredgewidth=0.7, markersize=10,
                              label="planted circular system"))
    if potential:
        handles.append(Line2D([0], [0], marker="X", ls="",
                              markerfacecolor="none", markeredgecolor="black",
                              markeredgewidth=0.7, markersize=8,
                              label="potentially circular system"))
    ax.legend(handles=handles, loc="upper left", fontsize=7, frameon=False)


def plot_reveal(tested: ScoreMatrix, reference: ScoreMatrix, swap: SwapResult,
                value: ValueResult, *, ax=None, planted=frozenset(),
                potential=frozenset(), xlabel="tested nugget bank",
                ylabel="reference nugget bank", title=None, window=None,
                legend=True, box_alpha=0.06):
    """Scatter every system at (mean under tested, mean under reference). Each
    point carries a margin box of half-width ``d_tested / 2`` and half-height
    ``d_reference / 2``, so two boxes overlap on an axis exactly when that
    leaderboard cannot separate the pair. The Theil-Sen fit is drawn with its
    ``+- d_residual`` value-test band in the tested (x) direction. Fill records
    the reveal, red for both tests, light blue for the swap test only, gold for
    the value test only. Planted systems are stars and potentially circular ones
    crosses, filled the same way or hollow when no test reveals them."""
    if ax is None:
        _, ax = plt.subplots(figsize=(4.5, 4.5))
    x = tested.values.mean(axis=1)
    y = reference.values.mean(axis=1)
    pos = {s: (float(x[i]), float(y[i])) for i, s in enumerate(tested.systems)}
    planted = frozenset(s for s in planted if s in pos)
    potential = frozenset(s for s in potential if s in pos)
    fill = {"both": swap.revealed & value.revealed,
            "swap": swap.revealed - value.revealed,
            "value": value.revealed - swap.revealed}
    hw, hh = swap.d_tested / 2, swap.d_reference / 2

    if window is None:
        pad = 0.1
        xlo, xhi = float(x.min()) - hw - pad, float(x.max()) + hw + pad
        ylo, yhi = float(y.min()) - hh - pad, float(y.max()) + hh + pad
    else:
        xlo, xhi, ylo, yhi = window

    for xi, yi in zip(x, y):
        ax.add_patch(Rectangle((xi - hw, yi - hh), 2 * hw, 2 * hh,
                               facecolor="0.30", alpha=box_alpha,
                               edgecolor="none", zorder=1))

    a, b, d_e = value.intercept, value.slope, value.d_residual
    ax.plot([a + b * ylo, a + b * yhi], [ylo, yhi], color="0.55", lw=0.9,
            zorder=2)
    for off in (d_e, -d_e):
        ax.plot([a + b * ylo + off, a + b * yhi + off], [ylo, yhi],
                color="0.55", lw=0.7, ls="--", zorder=2)

    revealed = swap.revealed | value.revealed
    marked = set(planted) | set(potential)

    def scatter(points, **kw):
        if points:
            xs, ys = zip(*points)
            ax.scatter(xs, ys, edgecolors="black", linewidths=0.7, **kw)

    scatter([pos[s] for s in tested.systems
             if s not in revealed and s not in marked],
            marker="o", s=20, facecolors="none", zorder=4)
    for key, color, _ in _FILL:
        scatter([pos[s] for s in fill[key] if s not in marked],
                marker="o", s=26, facecolors=color, alpha=0.85, zorder=5)
    for group, marker, size in ((planted, "*", 110), (potential, "X", 70)):
        for key, color, _ in _FILL:
            scatter([pos[s] for s in group if s in fill[key]],
                    marker=marker, s=size, facecolors=color, alpha=0.85,
                    zorder=6)
        scatter([pos[s] for s in group if s not in revealed],
                marker=marker, s=size, facecolors="none", zorder=6)

    ax.set_xlim(xlo, xhi)
    ax.set_ylim(ylo, yhi)
    if xlabel:
        ax.set_xlabel(xlabel)
    if ylabel:
        ax.set_ylabel(ylabel)
    if title:
        ax.set_title(title)
    if legend:
        _legend(ax, planted, potential)
    return ax

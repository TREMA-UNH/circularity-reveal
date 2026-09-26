"""circularity-reveal: reveal circular systems from paired nugget-bank
leaderboards, with a swap test and a value test."""
from .matrix import ScoreMatrix, align
from .reveal import (
    SwapResult,
    ValueResult,
    critical_difference,
    swap_test,
    theil_sen,
    value_test,
)

__all__ = [
    "ScoreMatrix",
    "align",
    "critical_difference",
    "theil_sen",
    "swap_test",
    "value_test",
    "SwapResult",
    "ValueResult",
]

try:
    from .plot import plot_reveal
except ImportError:  # matplotlib is an optional extra
    pass
else:
    __all__.append("plot_reveal")

__version__ = "0.1.0"

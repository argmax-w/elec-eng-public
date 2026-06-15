"""Nonlinear-dynamics experiments: the logistic map, the Mandelbrot set and a
Kuramoto model of cicada chorus synchronisation.

The library is small. Each module holds the vectorised numerics for one system,
with the narrative and figures kept in the paired notebooks.
"""

from __future__ import annotations

__version__ = "0.1.0"

__all__ = [
    "kuramoto",
    "logistic",
    "mandelbrot",
    "plotting",
]

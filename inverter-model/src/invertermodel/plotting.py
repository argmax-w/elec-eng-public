"""Shared figure helpers.

A single matplotlib style and a small named colour palette keep every figure in
the project consistent. The time axis is in milliseconds throughout, since the
PWM carrier and the mains cycle differ by five orders of magnitude and the
readable window sits in the millisecond range.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt

_PALETTE = {
    "boost": "#1f5673",
    "pwm": "#c44536",
    "filtered": "#3a7d44",
    "reference": "#5d8aa8",
    "error": "#7a4988",
    "spectrum": "#e8a13a",
}


def setup_style() -> None:
    """Apply the project's matplotlib style."""
    plt.rcParams.update(
        {
            "figure.figsize": (11, 4),
            "figure.dpi": 110,
            "axes.grid": True,
            "grid.alpha": 0.25,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "font.size": 10,
            "axes.titlesize": 11,
            "axes.titleweight": "semibold",
            "legend.frameon": False,
        }
    )


def palette(name: str) -> str:
    """Colour for a named signal family."""
    return _PALETTE[name]


def save_figure(fig: plt.Figure, name: str, figures_dir: Path) -> Path:
    """Save a figure for the README, returning its path."""
    figures_dir.mkdir(parents=True, exist_ok=True)
    path = figures_dir / f"{name}.png"
    fig.savefig(path, bbox_inches="tight", dpi=150)
    return path

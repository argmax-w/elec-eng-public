"""Shared figure helpers.

A small named palette and one style function keep the figures across the
notebooks consistent. Matplotlib only; no external theming. Axis labels are
lowercase and titles sentence-case, matching the rest of the portfolio.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt

_PALETTE = {
    "orbit": "#1f5673",
    "attractor": "#163b4e",
    "stable": "#2a7f62",
    "chaotic": "#c44536",
    "diagonal": "#56514c",
    "accent": "#7a4988",
    "highlight": "#e8a13a",
}


def setup_style() -> None:
    """Apply the project's matplotlib style."""
    plt.rcParams.update(
        {
            "figure.figsize": (9, 4.5),
            "figure.dpi": 110,
            "axes.grid": True,
            "grid.alpha": 0.25,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "font.size": 10,
            "axes.titlesize": 11,
            "axes.titleweight": "semibold",
            "legend.frameon": False,
            "image.cmap": "magma",
        }
    )


def palette(name: str) -> str:
    """Colour for a named series family."""
    return _PALETTE[name]


def save_figure(fig: plt.Figure, name: str, figures_dir: Path) -> Path:
    """Save a figure for the README, returning its path."""
    figures_dir = Path(figures_dir)
    figures_dir.mkdir(parents=True, exist_ok=True)
    path = figures_dir / f"{name}.png"
    fig.savefig(path, bbox_inches="tight", dpi=150)
    return path

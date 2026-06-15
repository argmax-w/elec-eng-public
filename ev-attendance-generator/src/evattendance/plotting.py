"""Shared figure helpers for the ev-attendance-generator project."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt

_PALETTE = {
    "customer": "#1f5673",
    "employee": "#e8a13a",
    "total": "#c44536",
    "arrival": "#2a7f62",
    "departure": "#7a4988",
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
    """Colour for a named category or distribution."""
    return _PALETTE[name]


def save_figure(fig: plt.Figure, name: str, figures_dir: str | Path) -> Path:
    """Save a figure for the README, returning its path."""
    figures_dir = Path(figures_dir)
    figures_dir.mkdir(parents=True, exist_ok=True)
    path = figures_dir / f"{name}.png"
    fig.savefig(path, bbox_inches="tight", dpi=150)
    return path

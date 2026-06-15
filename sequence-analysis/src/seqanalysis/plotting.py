"""Shared figure helpers for the sequence-analysis project.

A single matplotlib style and a small named palette keep the phase channels and
the three sequence components coloured consistently across every figure.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

# Phase channels share three colours; the sequence components have their own.
_PALETTE = {
    "Va": "#1f5673",
    "Vb": "#c44536",
    "Vc": "#e8a13a",
    "Ia": "#1f5673",
    "Ib": "#c44536",
    "Ic": "#e8a13a",
    "P": "#2a7f62",
    "N": "#c44536",
    "Z": "#5b5b7a",
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
    """Colour for a named phase channel or sequence component."""
    return _PALETTE[name]


def plot_sequence_series(
    ax: plt.Axes,
    table: pd.DataFrame,
    value: str,
    ylabel: str,
) -> None:
    """Plot one value column against time, one line per sequence component.

    Parameters
    ----------
    ax
        Target axes.
    table
        Output of :func:`seqanalysis.sequence.decompose_symmetrical_components`
        or :func:`harmonic_sequence_spectrum`, already filtered to one phase
        kind.
    value
        Column to draw, e.g. ``"amplitude"`` or ``"phase_offset_deg"``.
    ylabel
        Axis label including units.
    """
    for label in ("P", "N", "Z"):
        component = table[table["sequence"] == label]
        if component.empty:
            continue
        ax.plot(
            component["time_s"],
            component[value],
            color=_PALETTE[label],
            lw=1.2,
            label=f"{label} ({_sequence_word(label)})",
        )
    ax.set_xlabel("time (s)")
    ax.set_ylabel(ylabel)
    ax.legend()


def _sequence_word(label: str) -> str:
    return {"P": "positive", "N": "negative", "Z": "zero"}[label]


def save_figure(fig: plt.Figure, name: str, figures_dir: str | Path) -> Path:
    """Save a figure for the README, returning its path."""
    figures_dir = Path(figures_dir)
    figures_dir.mkdir(parents=True, exist_ok=True)
    path = figures_dir / f"{name}.png"
    fig.savefig(path, bbox_inches="tight", dpi=150)
    return path

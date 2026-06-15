"""Sweep the logistic map for its bifurcation diagram and Lyapunov exponent.

The two diagnostics are the heavy computation behind notebook 02, so they run
here. The attractor sample and the Lyapunov exponent over a fine grid of growth
rates are written to ``artifacts/bifurcation.npz``, and the paired figure the
README shows is rendered into ``reports/figures/``.

Usage:
    python scripts/run_bifurcation.py
    python scripts/run_bifurcation.py --grid 6000
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from nldynamics.logistic import bifurcation, lyapunov_exponent
from nldynamics.plotting import palette, save_figure, setup_style

REPO_ROOT = Path(__file__).resolve().parents[1]


def save_bifurcation_figure(
    r_grid: np.ndarray,
    r_points: np.ndarray,
    x_points: np.ndarray,
    exponent: np.ndarray,
    figures_dir: Path,
) -> Path:
    """Render the stacked bifurcation diagram and Lyapunov exponent."""
    setup_style()
    fig, (ax_bif, ax_lyap) = plt.subplots(2, 1, figsize=(9, 8), sharex=True)

    ax_bif.plot(r_points, x_points, ",", color=palette("attractor"), alpha=0.25)
    ax_bif.set_xlim(2.5, 4.0)
    ax_bif.set_ylim(0, 1)
    ax_bif.set_ylabel("attractor x")
    ax_bif.set_title("Bifurcation diagram of the logistic map")

    ax_lyap.axhline(0.0, color=palette("diagonal"), lw=0.8)
    stable = exponent < 0
    ax_lyap.plot(
        r_grid[stable], exponent[stable], ".", color=palette("stable"), ms=1.0, label="stable"
    )
    ax_lyap.plot(
        r_grid[~stable], exponent[~stable], ".", color=palette("chaotic"), ms=1.0, label="chaotic"
    )
    ax_lyap.set_xlim(2.5, 4.0)
    ax_lyap.set_ylim(-2, 1)
    ax_lyap.set_xlabel("growth rate r")
    ax_lyap.set_ylabel("Lyapunov exponent")
    ax_lyap.set_title("Lyapunov exponent: negative where stable, positive in chaos")
    ax_lyap.legend(loc="lower left", markerscale=6)

    fig.tight_layout()
    path = save_figure(fig, "bifurcation_lyapunov", figures_dir)
    plt.close(fig)
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--grid", type=int, default=4000, help="number of growth rates")
    parser.add_argument("--iterations", type=int, default=1000, help="iterations per growth rate")
    parser.add_argument("--last", type=int, default=100, help="attractor iterates kept")
    parser.add_argument(
        "--out",
        type=Path,
        default=REPO_ROOT / "artifacts" / "bifurcation.npz",
        help="output .npz path",
    )
    parser.add_argument(
        "--figures-dir",
        type=Path,
        default=REPO_ROOT / "reports" / "figures",
        help="output directory for the README figure",
    )
    args = parser.parse_args()

    r_grid = np.linspace(2.5, 4.0, args.grid)
    r_points, x_points = bifurcation(r_grid, iterations=args.iterations, last=args.last)
    exponent = lyapunov_exponent(r_grid, iterations=args.iterations, discard=args.last)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        args.out,
        r_grid=r_grid,
        r_points=r_points,
        x_points=x_points,
        exponent=exponent,
    )
    figure_path = save_bifurcation_figure(r_grid, r_points, x_points, exponent, args.figures_dir)
    print(f"{r_points.size:,} attractor points over {args.grid:,} growth rates -> {args.out}")
    print(f"figure -> {figure_path}")


if __name__ == "__main__":
    main()

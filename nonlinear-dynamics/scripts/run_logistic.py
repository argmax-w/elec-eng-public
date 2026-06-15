"""Iterate the logistic map and archive the trajectories and parameter sweep.

Notebook 01 reads the results from here rather than iterating in the notebook.
Four representative trajectories (a stable fixed point, period-two, period-four
and chaos) and a coarse attractor sweep that previews the bifurcation diagram
are written to ``artifacts/logistic.npz``.

Usage:
    python scripts/run_logistic.py
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from nldynamics.logistic import iterate

REPO_ROOT = Path(__file__).resolve().parents[1]

# Growth rates picked to land one in each regime of the cascade.
REGIME_R = (2.5, 3.2, 3.5, 3.9)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--length", type=int, default=60, help="trajectory length to keep")
    parser.add_argument("--sweep-points", type=int, default=600, help="growth rates in the sweep")
    parser.add_argument(
        "--out",
        type=Path,
        default=REPO_ROOT / "artifacts" / "logistic.npz",
        help="output .npz path",
    )
    args = parser.parse_args()

    trajectories = np.stack([iterate(r, 0.2, n=args.length, discard=200) for r in REGIME_R])

    sweep_r_grid = np.linspace(2.5, 4.0, args.sweep_points)
    sweep_r, sweep_x = [], []
    for r in sweep_r_grid:
        attractor = iterate(r, 0.2, n=40, discard=400)
        sweep_r.append(np.full_like(attractor, r))
        sweep_x.append(attractor)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        args.out,
        regime_r=np.array(REGIME_R),
        trajectories=trajectories,
        sweep_r=np.concatenate(sweep_r),
        sweep_x=np.concatenate(sweep_x),
    )
    print(f"{len(REGIME_R)} trajectories and a {args.sweep_points}-point sweep -> {args.out}")


if __name__ == "__main__":
    main()

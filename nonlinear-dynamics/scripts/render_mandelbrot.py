"""Render the documented Mandelbrot windows and archive their escape counts.

Each window in :data:`nldynamics.mandelbrot.ZOOMS` is rendered by escape-time
iteration. The escape-count arrays are the heavy computation behind notebook 03,
so they are written to ``artifacts/mandelbrot.npz`` for the notebook to load,
and the committed PNGs the README shows are saved into ``reports/figures/``.

Usage:
    python scripts/render_mandelbrot.py
    python scripts/render_mandelbrot.py --zoom seahorse --cmap inferno
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from nldynamics.mandelbrot import ZOOMS, escape_counts
from nldynamics.plotting import save_figure, setup_style

REPO_ROOT = Path(__file__).resolve().parents[1]


def render(name: str, counts: np.ndarray, figures_dir: Path, *, cmap: str) -> Path:
    """Render a precomputed escape-count image and save it."""
    region = ZOOMS[name]
    fig, ax = plt.subplots(figsize=(7, 7 * region.aspect))
    ax.imshow(
        counts,
        extent=region.extent,
        origin="lower",
        cmap=cmap,
        interpolation="bilinear",
    )
    ax.set_xlabel("real part of c")
    ax.set_ylabel("imaginary part of c")
    ax.set_title(f"Mandelbrot set: {name} window")
    ax.grid(False)
    path = save_figure(fig, f"mandelbrot_{name}", figures_dir)
    plt.close(fig)
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--zoom",
        choices=[*ZOOMS, "all"],
        default="all",
        help="which window to render",
    )
    parser.add_argument(
        "--figures-dir",
        type=Path,
        default=REPO_ROOT / "reports" / "figures",
        help="output directory for the PNGs",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=REPO_ROOT / "artifacts" / "mandelbrot.npz",
        help="output .npz path for the escape-count arrays",
    )
    parser.add_argument("--cmap", default="magma", help="matplotlib colour map")
    args = parser.parse_args()

    setup_style()
    names = list(ZOOMS) if args.zoom == "all" else [args.zoom]
    arrays: dict[str, np.ndarray] = {}
    for name in names:
        region = ZOOMS[name]
        counts = escape_counts(region)
        arrays[name] = counts
        arrays[f"{name}_extent"] = np.array(region.extent)
        path = render(name, counts, args.figures_dir, cmap=args.cmap)
        print(f"rendered {name} ({counts.shape[1]}x{counts.shape[0]}) -> {path}")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(args.out, **arrays)
    print(f"escape-count arrays -> {args.out}")


if __name__ == "__main__":
    main()

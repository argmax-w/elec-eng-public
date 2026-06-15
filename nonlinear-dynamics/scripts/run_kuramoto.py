"""Run a Kuramoto simulation, sweep the coupling and archive the results.

This is the computation behind notebook 04, kept out of the notebook. A single
run gives the phase history and order-parameter curve; a coupling sweep records
the final coherence of an otherwise identical run at each strength, tracing the
synchronisation threshold. Everything is written to ``artifacts/kuramoto.npz``,
and the order-parameter curve the README shows is rendered into
``reports/figures/``.

Usage:
    python scripts/run_kuramoto.py
    python scripts/run_kuramoto.py --coupling 2.0 --oscillators 80
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from nldynamics.kuramoto import order_parameter, simulate_kuramoto
from nldynamics.plotting import palette, save_figure, setup_style

REPO_ROOT = Path(__file__).resolve().parents[1]


def save_order_parameter_figure(
    times: np.ndarray,
    coherence: np.ndarray,
    coupling: float,
    figures_dir: Path,
) -> Path:
    """Render the coherence-over-time curve for the README."""
    setup_style()
    fig, ax = plt.subplots()
    ax.plot(times, coherence, color=palette("orbit"), lw=1.4)
    ax.set_ylim(0, 1)
    ax.set_xlabel("time (s)")
    ax.set_ylabel("phase coherence |r|")
    ax.set_title(f"Kuramoto synchronisation, coupling K = {coupling:g}")
    path = save_figure(fig, "kuramoto_order_parameter", figures_dir)
    plt.close(fig)
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--oscillators", type=int, default=50, help="number of oscillators")
    parser.add_argument("--coupling", type=float, default=1.5, help="coupling strength K")
    parser.add_argument(
        "--frequency-spread",
        type=float,
        default=0.4,
        help="standard deviation of natural angular frequencies",
    )
    parser.add_argument("--steps", type=int, default=3000, help="integration steps")
    parser.add_argument("--dt", type=float, default=0.01, help="time step, seconds")
    parser.add_argument("--seed", type=int, default=0, help="random seed")
    parser.add_argument("--sweep-points", type=int, default=16, help="coupling values in the sweep")
    parser.add_argument(
        "--sweep-max", type=float, default=3.0, help="largest coupling in the sweep"
    )
    parser.add_argument("--sweep-steps", type=int, default=2000, help="steps per sweep run")
    parser.add_argument(
        "--out",
        type=Path,
        default=REPO_ROOT / "artifacts" / "kuramoto.npz",
        help="output .npz path",
    )
    parser.add_argument(
        "--figures-dir",
        type=Path,
        default=REPO_ROOT / "reports" / "figures",
        help="output directory for the README figure",
    )
    args = parser.parse_args()

    result = simulate_kuramoto(
        args.oscillators,
        args.coupling,
        frequency_spread=args.frequency_spread,
        steps=args.steps,
        dt=args.dt,
        seed=args.seed,
    )
    coherence, mean_phase = order_parameter(result.phases)

    # Coupling sweep: the final coherence of an otherwise identical run at each
    # strength traces the synchronisation threshold.
    sweep_couplings = np.linspace(0.0, args.sweep_max, args.sweep_points)
    sweep_final = []
    for k in sweep_couplings:
        run = simulate_kuramoto(
            args.oscillators,
            k,
            frequency_spread=args.frequency_spread,
            steps=args.sweep_steps,
            dt=args.dt,
            seed=args.seed,
        )
        run_coherence, _ = order_parameter(run.phases)
        sweep_final.append(run_coherence[-200:].mean())
    sweep_final_coherence = np.array(sweep_final)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        args.out,
        times=result.times,
        phases=result.phases,
        natural_frequencies=result.natural_frequencies,
        coherence=coherence,
        mean_phase=mean_phase,
        coupling=np.array(result.coupling),
        sweep_couplings=sweep_couplings,
        sweep_final_coherence=sweep_final_coherence,
    )
    figure_path = save_order_parameter_figure(
        result.times, coherence, result.coupling, args.figures_dir
    )
    final = coherence[-200:].mean()
    print(
        f"simulated {args.oscillators} oscillators at K={args.coupling}; "
        f"final coherence {final:.3f} -> {args.out}"
    )
    print(f"coupling sweep: {args.sweep_points} runs to K={args.sweep_max}")
    print(f"figure -> {figure_path}")


if __name__ == "__main__":
    main()

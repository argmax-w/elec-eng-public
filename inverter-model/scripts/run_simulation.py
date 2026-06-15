"""Run the grid-following inverter simulation and write its time series.

Integrates the cascaded boost-PWM-filter-PLL model over the configured horizon
and saves the recorded waveforms to ``artifacts/sim.npz`` with a small JSON of
run metadata (timing, lock metrics, the operating-point sizing). The notebook
only reads these artifacts, so the heavy loop runs once here.

Usage
-----
    python scripts/run_simulation.py [--config path/to/config.yaml]
"""

from __future__ import annotations

import argparse
import json
import time as timing

import numpy as np
from invertermodel.config import load_config
from invertermodel.power import power_settings
from invertermodel.simulation import simulate


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=None, help="path to a configuration YAML")
    args = parser.parse_args()

    cfg = load_config(args.config)
    n_steps = round(cfg.simulation.duration / cfg.simulation.timestep)
    print(
        f"simulating {cfg.simulation.duration} s at {cfg.simulation.timestep} s ({n_steps} steps)",
        flush=True,
    )

    start = timing.perf_counter()
    result = simulate(cfg)
    elapsed = timing.perf_counter() - start
    print(f"integration finished in {elapsed:.1f} s", flush=True)

    operating_point = power_settings(
        cfg.power.active_power,
        cfg.power.reactive_power,
        cfg.power.tie_inductance,
        cfg.power.grid_amplitude,
    )

    # Lock metrics: the residual between the filtered output (normalised to its
    # settled amplitude) and the grid reference, and the spread of the phase
    # error before and after the loop settles.
    settled = result.filtered_voltage[result.settled]
    amplitude = float(np.abs(settled).max())
    normalised = result.filtered_voltage / amplitude
    residual = result.reference - normalised
    transient = result.phase_error[: result.settle_index]
    locked = result.phase_error[result.settle_index :]

    cfg.paths.artifacts.mkdir(parents=True, exist_ok=True)
    npz_path = cfg.paths.artifacts / "sim.npz"
    np.savez_compressed(
        npz_path,
        time=result.time.astype(np.float32),
        boost_voltage=result.boost_voltage.astype(np.float32),
        pwm_voltage=result.pwm_voltage.astype(np.float32),
        filtered_voltage=result.filtered_voltage.astype(np.float32),
        reference=result.reference.astype(np.float32),
        phase_error=result.phase_error.astype(np.float32),
        residual=residual.astype(np.float32),
    )

    meta = {
        "n_steps": int(result.time.size),
        "duration_s": cfg.simulation.duration,
        "timestep_s": cfg.simulation.timestep,
        "grid_frequency_hz": cfg.grid.frequency,
        "settle_index": int(result.settle_index),
        "runtime_s": round(elapsed, 3),
        "boost_final_voltage": float(result.boost_voltage[-1]),
        "filtered_settled_amplitude": amplitude,
        "phase_error_transient_std": float(transient.std()),
        "phase_error_locked_std": float(locked.std()),
        "phase_error_locked_mean": float(locked.mean()),
        "operating_point": {
            "current_magnitude": operating_point.current_magnitude,
            "current_angle_rad": operating_point.current_angle,
            "inverter_magnitude": operating_point.inverter_magnitude,
            "inverter_angle_rad": operating_point.inverter_angle,
        },
    }
    meta_path = cfg.paths.artifacts / "sim_meta.json"
    meta_path.write_text(json.dumps(meta, indent=2) + "\n")

    print(
        f"boost output settled at {meta['boost_final_voltage']:.2f} V; "
        f"phase-error spread {meta['phase_error_transient_std']:.2f} -> "
        f"{meta['phase_error_locked_std']:.2f} as the loop locks",
        flush=True,
    )
    print(f"artifacts written to {npz_path} and {meta_path}")


if __name__ == "__main__":
    main()

"""Generate the synthetic charging-demand profile and write it to artifacts.

Builds the fitted fleet, samples occupancy across the day, aggregates the load
curve and stores the arrival and departure densities alongside it; the notebook
reads these back and draws them. The withheld engine and fitted parameters must
be present (decrypted) for this to run.

Usage:
    python scripts/generate_profiles.py
    python scripts/generate_profiles.py --config config/profiles.example.yaml
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd
from evattendance.profiles import (
    ENGINE_AVAILABLE,
    TIME_GRID,
    build_demand_profile,
    build_mixture_pdf,
    default_fleet,
    load_fleet_config,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = REPO_ROOT / "artifacts"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config", type=Path, default=None, help="fleet YAML; default uses the fitted fleet"
    )
    parser.add_argument("--seed", type=int, default=0, help="random seed")
    args = parser.parse_args()

    if not ENGINE_AVAILABLE:
        raise SystemExit(
            "The generation engine and fitted parameters are withheld and not "
            "decrypted in this checkout, so the profile cannot be regenerated here. "
            "The committed notebook already carries the results."
        )

    fleet = load_fleet_config(args.config) if args.config else default_fleet()
    profile = build_demand_profile(fleet, TIME_GRID, seed=args.seed)

    densities = pd.DataFrame({"hour": TIME_GRID})
    for spec in fleet:
        densities[f"{spec.name}_arrival"] = build_mixture_pdf(spec.arrival, TIME_GRID)
        densities[f"{spec.name}_departure"] = build_mixture_pdf(spec.departure, TIME_GRID)

    ARTIFACTS.mkdir(exist_ok=True)
    profile.to_parquet(ARTIFACTS / "profile.parquet")
    densities.to_parquet(ARTIFACTS / "densities.parquet")
    meta = {
        "categories": [
            {"name": spec.name, "fleet_size": spec.fleet_size, "charger_kw": spec.charger_kw}
            for spec in fleet
        ],
        "peak_total_kw": float(profile["load_total_kw"].max()),
        "seed": args.seed,
    }
    (ARTIFACTS / "meta.json").write_text(json.dumps(meta, indent=2))
    print(
        f"profile for {len(fleet)} categories written to {ARTIFACTS}; "
        f"peak total load {meta['peak_total_kw']:.0f} kW"
    )


if __name__ == "__main__":
    main()

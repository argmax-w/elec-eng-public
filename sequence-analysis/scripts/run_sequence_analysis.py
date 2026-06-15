"""Run the sequence decomposition and write its tables to artifacts.

The sliding-window decomposition is the heavy step, so it runs here and lands in
``artifacts/`` as parquet; the notebooks read those tables and concentrate on
the narrative and the figures. The withheld kernel must be present (decrypted)
for this to run; without it the decomposition raises a clear error.

Usage:
    python scripts/run_sequence_analysis.py
    python scripts/run_sequence_analysis.py --data data/raw/BigBatt_telem.csv
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from seqanalysis.io import PHASE_CURRENT, PHASE_VOLTAGE, load_telemetry
from seqanalysis.sequence import (
    KERNEL_AVAILABLE,
    decompose_symmetrical_components,
    harmonic_sequence_spectrum,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA = REPO_ROOT / "data" / "raw" / "BigBatt_telem.csv"
ARTIFACTS = REPO_ROOT / "artifacts"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA, help="telemetry CSV")
    parser.add_argument("--base-frequency", type=float, default=50.0, help="fundamental, Hz")
    args = parser.parse_args()

    if not KERNEL_AVAILABLE:
        raise SystemExit(
            "The sequence-decomposition kernel is withheld and not decrypted in this "
            "checkout, so the analysis cannot be recomputed here. The committed "
            "notebooks already carry the results."
        )

    telemetry = load_telemetry(args.data, base_frequency=args.base_frequency)
    window = telemetry.samples_per_cycle
    print(
        f"loaded {len(telemetry.frame)} samples at {telemetry.sample_interval * 1e6:.0f} us "
        f"({telemetry.samples_per_cycle} samples per {args.base_frequency:.0f} Hz cycle)"
    )

    ARTIFACTS.mkdir(exist_ok=True)
    for phases, name in ((tuple(PHASE_VOLTAGE), "voltage"), (tuple(PHASE_CURRENT), "current")):
        symmetrical = decompose_symmetrical_components(
            telemetry.frame, phases, window, telemetry.sample_interval
        )
        symmetrical.to_parquet(ARTIFACTS / f"symmetrical_{name}.parquet")

        harmonic = harmonic_sequence_spectrum(
            telemetry.frame, phases, window, telemetry.sample_interval, args.base_frequency
        )
        harmonic.to_parquet(ARTIFACTS / f"harmonic_{name}.parquet")
        print(f"{name}: {len(symmetrical)} symmetrical rows, {len(harmonic)} harmonic rows")

    meta = {
        "sample_interval_s": telemetry.sample_interval,
        "samples_per_cycle": telemetry.samples_per_cycle,
        "base_frequency_hz": args.base_frequency,
        "n_samples": len(telemetry.frame),
        "duration_s": telemetry.duration,
    }
    (ARTIFACTS / "meta.json").write_text(json.dumps(meta, indent=2))
    print(f"artifacts written to {ARTIFACTS}")


if __name__ == "__main__":
    main()

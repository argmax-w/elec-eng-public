"""Tests for the telemetry loader."""

from __future__ import annotations

import numpy as np
import pandas as pd
from seqanalysis.io import PHASE_CURRENT, PHASE_VOLTAGE, load_telemetry


def _write_synthetic_csv(path, n=300, fs=1600.0, f0=50.0):
    """Write a balanced three-phase record in the expected schema."""
    t = np.arange(n) / fs
    start = pd.Timestamp("2024-11-13 17:14:16")
    stamps = start + pd.to_timedelta(t, unit="s")
    phases = [0.0, -2 * np.pi / 3, 2 * np.pi / 3]
    frame = pd.DataFrame(
        {
            "Timestamp (Client Local) Eastern Australia Time": stamps,
            "Timestamp (Device Local) Eastern Australia Time": stamps,
            "V1": 1000.0 * np.cos(2 * np.pi * f0 * t + phases[0]),
            "V2": 1000.0 * np.cos(2 * np.pi * f0 * t + phases[1]),
            "V3": 1000.0 * np.cos(2 * np.pi * f0 * t + phases[2]),
            "I1": np.cos(2 * np.pi * f0 * t + phases[0]),
            "I2": np.cos(2 * np.pi * f0 * t + phases[1]),
            "I3": np.cos(2 * np.pi * f0 * t + phases[2]),
        }
    )
    frame.to_csv(path, index=False)


def test_columns_renamed_and_timed(tmp_path):
    csv = tmp_path / "telem.csv"
    _write_synthetic_csv(csv)
    telemetry = load_telemetry(csv)

    assert list(telemetry.frame.columns) == ["time_s", *PHASE_VOLTAGE, *PHASE_CURRENT]
    assert telemetry.frame["time_s"].iloc[0] == 0.0
    assert telemetry.frame["time_s"].is_monotonic_increasing


def test_sampling_and_cycle_length(tmp_path):
    csv = tmp_path / "telem.csv"
    _write_synthetic_csv(csv, fs=1600.0, f0=50.0)
    telemetry = load_telemetry(csv, base_frequency=50.0)

    assert telemetry.sample_interval == 1 / 1600.0
    # 1600 Hz / 50 Hz = 32 samples per cycle.
    assert telemetry.samples_per_cycle == 32

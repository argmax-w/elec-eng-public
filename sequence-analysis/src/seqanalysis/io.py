"""Load and tidy the three-phase battery telemetry.

The raw export carries client-local timestamps (Eastern Australia Time) and the
six instantaneous channels ``V1``-``V3`` and ``I1``-``I3``. This module reads it
into a frame with the conventional phase labels ``Va``-``Vc`` and ``Ia``-``Ic``,
recovers the sampling interval from the timestamps and reports how many samples
fall in one fundamental cycle, which sets the decomposition window downstream.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

CLIENT_TIME_COLUMN = "Timestamp (Client Local) Eastern Australia Time"
RAW_VOLTAGE = ["V1", "V2", "V3"]
RAW_CURRENT = ["I1", "I2", "I3"]
PHASE_VOLTAGE = ["Va", "Vb", "Vc"]
PHASE_CURRENT = ["Ia", "Ib", "Ic"]


@dataclass(frozen=True)
class Telemetry:
    """A tidy telemetry record and the timing it implies.

    Attributes
    ----------
    frame
        Columns ``time_s`` (seconds from the first sample) and the six phase
        channels ``Va``-``Vc``, ``Ia``-``Ic``.
    sample_interval
        Median seconds between consecutive samples.
    samples_per_cycle
        Samples in one fundamental period, ``round(1 / (f0 * dt))``.
    base_frequency
        Assumed fundamental frequency in hertz.
    """

    frame: pd.DataFrame
    sample_interval: float
    samples_per_cycle: int
    base_frequency: float

    @property
    def duration(self) -> float:
        """Total record length in seconds."""
        return len(self.frame) * self.sample_interval


def load_telemetry(path: str | Path, base_frequency: float = 50.0) -> Telemetry:
    """Read the telemetry CSV into a :class:`Telemetry` record.

    Parameters
    ----------
    path
        Path to the telemetry CSV.
    base_frequency
        Fundamental frequency of the system, hertz. The NEM runs at 50 Hz.

    Returns
    -------
    Telemetry
        The tidy frame and the timing recovered from the timestamps.
    """
    path = Path(path)
    raw = pd.read_csv(path)

    timestamps = pd.to_datetime(raw[CLIENT_TIME_COLUMN])
    sample_interval = float(timestamps.diff().dt.total_seconds().median())

    tidy = raw[RAW_VOLTAGE + RAW_CURRENT].copy()
    tidy.columns = PHASE_VOLTAGE + PHASE_CURRENT
    tidy.insert(0, "time_s", np.round(np.arange(len(tidy)) * sample_interval, 6))

    samples_per_cycle = round((1.0 / base_frequency) / sample_interval)
    return Telemetry(
        frame=tidy.reset_index(drop=True),
        sample_interval=sample_interval,
        samples_per_cycle=samples_per_cycle,
        base_frequency=base_frequency,
    )

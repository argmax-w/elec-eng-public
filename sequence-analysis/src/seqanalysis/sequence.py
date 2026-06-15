"""Sequence decomposition of three-phase telemetry.

Two views of the same record:

- :func:`decompose_symmetrical_components` tracks the zero, positive and
  negative sequence phasors over a sliding one-cycle window. It estimates each
  phase's fundamental phasor, maps the three through the inverse
  symmetrical-component transform, and records the sequence magnitudes and phase
  offsets against time. A balanced supply sits almost entirely in the positive
  sequence; negative and zero sequence growth flags an unbalanced fault.
- :func:`harmonic_sequence_spectrum` groups the windowed FFT into integer
  harmonic orders and averages by the sequence of each order.

The kernel that estimates the phasors and applies the transform is withheld
from the public release (see the README). With it present these functions run
and produce the committed figures; without it they raise a clear error.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

try:
    from ._kernel import (
        classify_harmonic_sequence,
        extract_fundamental,
        symmetrical_components,
    )

    KERNEL_AVAILABLE = True
except Exception:
    KERNEL_AVAILABLE = False

    def _withheld(*_args, **_kwargs):
        raise RuntimeError(
            "The sequence-decomposition kernel is withheld from the public "
            "release of this repository. The committed notebooks show the "
            "results it produces; the implementation is available on request."
        )

    extract_fundamental = symmetrical_components = classify_harmonic_sequence = _withheld

VOLTAGE_PHASES = ("Va", "Vb", "Vc")
CURRENT_PHASES = ("Ia", "Ib", "Ic")
# The transform returns the components in this order.
SEQUENCE_ORDER = ("Z", "P", "N")
SEQUENCE_NAME = {"Z": "zero", "P": "positive", "N": "negative"}


def _phase_kind(column: str) -> str:
    return "voltage" if column in VOLTAGE_PHASES else "current"


def decompose_symmetrical_components(
    frame: pd.DataFrame,
    phases: tuple[str, str, str],
    window_size: int,
    sample_interval: float,
) -> pd.DataFrame:
    """Track the symmetrical-sequence phasors over a sliding one-cycle window.

    Parameters
    ----------
    frame
        Telemetry frame holding at least the three named phase columns.
    phases
        The three phase columns in order, e.g. ``("Va", "Vb", "Vc")``.
    window_size
        Window length in samples; one fundamental cycle.
    sample_interval
        Seconds between samples, used to stamp each window with a time.

    Returns
    -------
    pandas.DataFrame
        One row per window and sequence, with columns ``window``, ``time_s``,
        ``phase_kind``, ``sequence``, ``amplitude``, ``phase_deg`` and
        ``phase_offset_deg`` (phase relative to the positive sequence).
    """
    channels = [frame[column].to_numpy() for column in phases]
    kind = _phase_kind(phases[0])
    n_samples = len(frame)
    rows: list[dict] = []

    for start in range(n_samples - window_size + 1):
        window = slice(start, start + window_size)
        phasors = []
        for channel in channels:
            amplitude, phase = extract_fundamental(channel[window])
            phasors.append(amplitude * np.exp(1j * phase))

        components = symmetrical_components(phasors)
        positive_phase = np.angle(components[1], deg=True)
        for label, component in zip(SEQUENCE_ORDER, components, strict=True):
            amplitude = float(np.abs(component))
            phase_deg = float(np.angle(component, deg=True))
            rows.append(
                {
                    "window": start,
                    "time_s": round(start * sample_interval, 6),
                    "phase_kind": kind,
                    "sequence": label,
                    "amplitude": amplitude if amplitude > 1e-5 else 0.0,
                    "phase_deg": phase_deg,
                    "phase_offset_deg": phase_deg - positive_phase,
                }
            )

    return pd.DataFrame(rows)


def harmonic_sequence_spectrum(
    frame: pd.DataFrame,
    phases: tuple[str, str, str],
    window_size: int,
    sample_interval: float,
    base_frequency: float = 50.0,
) -> pd.DataFrame:
    """Average the windowed harmonic spectrum by sequence class.

    For each window and phase the orthonormal real FFT is grouped to the nearest
    integer harmonic of ``base_frequency``; every harmonic is labelled positive,
    negative or zero sequence by its order, and the window's sequence magnitude
    and phase are the means over the harmonics in each class.

    Returns
    -------
    pandas.DataFrame
        One row per window, phase and sequence, with columns ``window``,
        ``time_s``, ``phase_kind``, ``column``, ``sequence``, ``magnitude`` and
        ``phase_deg``.
    """
    n_samples = len(frame)
    rows: list[dict] = []

    for start in range(n_samples - window_size + 1):
        window = frame.iloc[start : start + window_size]
        for column in phases:
            signal = window[column].to_numpy()
            spectrum = np.fft.rfft(signal, norm="ortho")
            freqs = np.fft.rfftfreq(len(signal), sample_interval)
            harmonics = np.array([classify_harmonic_sequence(f / base_frequency) for f in freqs])

            harmonic_frame = pd.DataFrame(
                {
                    "sequence": harmonics,
                    "magnitude": np.abs(spectrum),
                    "phase_deg": np.angle(spectrum, deg=True),
                }
            )
            harmonic_frame = harmonic_frame[harmonic_frame["sequence"].isin(SEQUENCE_ORDER)]
            averaged = harmonic_frame.groupby("sequence", as_index=False).mean()

            for record in averaged.to_dict("records"):
                rows.append(
                    {
                        "window": start,
                        "time_s": round(start * sample_interval, 6),
                        "phase_kind": _phase_kind(column),
                        "column": column,
                        "sequence": record["sequence"],
                        "magnitude": record["magnitude"],
                        "phase_deg": record["phase_deg"],
                    }
                )

    return pd.DataFrame(rows)

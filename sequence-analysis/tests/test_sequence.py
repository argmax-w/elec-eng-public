"""Tests for the public sequence interface.

These exercise the withheld kernel, so they are skipped when it is encrypted and
absent (for example on a public CI checkout). When the kernel is present they
check that a balanced supply reads as almost pure positive sequence.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from seqanalysis.sequence import (
    KERNEL_AVAILABLE,
    decompose_symmetrical_components,
    harmonic_sequence_spectrum,
)

pytestmark = pytest.mark.skipif(not KERNEL_AVAILABLE, reason="withheld kernel not decrypted")

FS = 1600.0
F0 = 50.0
WINDOW = 32


def _balanced_frame(n=320, unbalance=0.0):
    """Balanced three-phase voltages, optionally with phase A scaled down."""
    t = np.arange(n) / FS
    phases = [0.0, -2 * np.pi / 3, 2 * np.pi / 3]
    gains = [1.0 - unbalance, 1.0, 1.0]
    return pd.DataFrame(
        {
            "time_s": t,
            "Va": gains[0] * np.cos(2 * np.pi * F0 * t + phases[0]),
            "Vb": gains[1] * np.cos(2 * np.pi * F0 * t + phases[1]),
            "Vc": gains[2] * np.cos(2 * np.pi * F0 * t + phases[2]),
        }
    )


def test_balanced_supply_is_positive_sequence():
    frame = _balanced_frame()
    table = decompose_symmetrical_components(frame, ("Va", "Vb", "Vc"), WINDOW, 1 / FS)

    means = table.groupby("sequence")["amplitude"].mean()
    assert means["P"] > 0.9
    assert means["N"] < 1e-3
    assert means["Z"] < 1e-3


def test_unbalance_raises_negative_sequence():
    balanced = decompose_symmetrical_components(
        _balanced_frame(), ("Va", "Vb", "Vc"), WINDOW, 1 / FS
    )
    faulted = decompose_symmetrical_components(
        _balanced_frame(unbalance=0.3), ("Va", "Vb", "Vc"), WINDOW, 1 / FS
    )
    n_balanced = balanced.loc[balanced["sequence"] == "N", "amplitude"].mean()
    n_faulted = faulted.loc[faulted["sequence"] == "N", "amplitude"].mean()
    assert n_faulted > 10 * n_balanced


def test_harmonic_spectrum_labels_sequences():
    table = harmonic_sequence_spectrum(_balanced_frame(), ("Va", "Vb", "Vc"), WINDOW, 1 / FS, F0)
    assert set(table["sequence"]) <= {"P", "N", "Z"}
    assert not table.empty

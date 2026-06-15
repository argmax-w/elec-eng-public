"""Symmetrical-component and harmonic-sequence analysis of three-phase telemetry.

Reads three-phase voltage and current telemetry, estimates the fundamental
phasors cycle by cycle, and resolves them into zero, positive and negative
sequence components to read imbalance and fault signatures.

The kernel that does the phasor estimation and the transform is withheld from
the public release (see the README). The public interface is
:mod:`seqanalysis.sequence`.
"""

from __future__ import annotations

from .io import Telemetry, load_telemetry
from .sequence import (
    KERNEL_AVAILABLE,
    decompose_symmetrical_components,
    harmonic_sequence_spectrum,
)

__all__ = [
    "KERNEL_AVAILABLE",
    "Telemetry",
    "decompose_symmetrical_components",
    "harmonic_sequence_spectrum",
    "load_telemetry",
]

__version__ = "0.1.0"

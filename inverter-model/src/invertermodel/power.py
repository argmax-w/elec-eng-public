"""Operating-point sizing for an inductive grid tie.

A grid-following inverter delivers a specified apparent power into the grid
through a coupling inductor. The inverter cannot set its power directly; it sets
its terminal voltage, and the current that flows is fixed by the voltage
difference across the tie reactance. This module inverts that relationship: from
a requested active and reactive power it returns the line current and the
inverter terminal voltage required to drive it.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class OperatingPoint:
    """Line current and inverter voltage for a requested apparent power.

    Magnitudes are in the same units as the supplied grid voltage; arguments
    are in radians, referenced to the grid voltage phasor.
    """

    current_magnitude: float
    current_angle: float
    inverter_magnitude: float
    inverter_angle: float


def power_settings(
    p: float, q: float, tie_inductance: float, grid_amplitude: float
) -> OperatingPoint:
    """Inverter terminal voltage required for a requested apparent power.

    The grid voltage phasor is taken as the angle reference. The line current
    magnitude follows from the apparent power, ``|S| = sqrt(P^2 + Q^2)``, over
    the grid voltage; its angle is the power-factor angle ``arccos(P / (V |I|))``.
    The inverter voltage is then the grid voltage plus the drop across the
    series tie reactance ``j omega L``, here written with a per-unit reactance of
    ``L`` so the routine matches the operating-point sizing used in the
    simulation.

    Parameters
    ----------
    p
        Active power into the tie.
    q
        Reactive power into the tie.
    tie_inductance
        Series reactance of the coupling to the grid.
    grid_amplitude
        Grid voltage magnitude at the point of common coupling.

    Returns
    -------
    OperatingPoint
        Line-current and inverter-voltage magnitudes and angles.
    """
    current_magnitude = np.hypot(p, q) / grid_amplitude
    current_angle = np.arccos(p / (grid_amplitude * current_magnitude))

    current = current_magnitude * np.exp(1j * current_angle)
    inverter = current * 1j * tie_inductance + grid_amplitude
    return OperatingPoint(
        current_magnitude=float(current_magnitude),
        current_angle=float(current_angle),
        inverter_magnitude=float(np.abs(inverter)),
        inverter_angle=float(np.angle(inverter)),
    )

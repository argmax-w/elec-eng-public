"""Time-domain simulation of a grid-following inverter.

A boost converter, a sinusoidal pulse-width modulator, an output filter and an
analogue phase-locked loop are cascaded and integrated on a fixed time grid; the
loop synchronises the inverter output to a 50 Hz grid reference.
"""

from __future__ import annotations

from .config import Config, load_config
from .power import OperatingPoint, power_settings
from .simulation import SimulationResult, simulate

__version__ = "0.1.0"

__all__ = [
    "Config",
    "OperatingPoint",
    "SimulationResult",
    "load_config",
    "power_settings",
    "simulate",
]

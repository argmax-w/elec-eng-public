"""Synthetic car-park EV charging-demand profiles.

A small behavioural model turns a description of a vehicle fleet into a 24-hour
charging load curve: each category arrives and departs according to a
mixture-of-Gaussians distribution over the day, occupancy is counted across the
fleet and multiplied by the charger rating, and the categories are summed.

The generation engine and the fitted behavioural parameters are withheld from
the public release (see the README); the public interface is
:mod:`evattendance.profiles`.
"""

from __future__ import annotations

from .profiles import (
    ENGINE_AVAILABLE,
    TIME_GRID,
    CategorySpec,
    Mixture,
    MixtureComponent,
    build_demand_profile,
    load_fleet_config,
)

__all__ = [
    "ENGINE_AVAILABLE",
    "TIME_GRID",
    "CategorySpec",
    "Mixture",
    "MixtureComponent",
    "build_demand_profile",
    "load_fleet_config",
]

__version__ = "0.1.0"

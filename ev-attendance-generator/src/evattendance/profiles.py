"""Synthetic car-park charging-demand profiles.

A fleet is described by a list of :class:`CategorySpec`, one per behavioural
group (for example customers and employees). Each category has a mixture-of-
Gaussians arrival distribution and a departure distribution over the hour of the
day, a fleet size and a charger rating. :func:`build_demand_profile` samples
arrival and departure times for every vehicle, counts how many are present at
each time step and multiplies by the charger rating to get a load curve.

The generation engine (the distribution sampling, the constraint that a vehicle
leaves after it arrives, and the occupancy count) and the fitted behavioural
parameters are withheld from the public release: see the project README. The
data classes, the configuration loader and the orchestration here are open, and
an illustrative placeholder fleet ships in ``config/profiles.example.yaml`` so
the structure is clear; the fitted numbers behind the published load curve are
not included.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

# Hour-of-day grid at six-minute resolution, the time base for every profile.
TIME_GRID = np.arange(0.0, 24.0, 0.1)


@dataclass(frozen=True)
class MixtureComponent:
    """One Gaussian component of an arrival or departure distribution.

    ``mean`` and ``sigma`` are in hours of the day; ``weight`` is the relative
    contribution of this component before the mixture is normalised.
    """

    mean: float
    sigma: float
    weight: float


@dataclass(frozen=True)
class Mixture:
    """A weighted mixture of Gaussian components over the hour of the day."""

    components: tuple[MixtureComponent, ...]


@dataclass(frozen=True)
class CategorySpec:
    """A behavioural group of vehicles.

    Attributes
    ----------
    name
        Group label, used in the output column names.
    fleet_size
        Number of vehicles in the group.
    arrival, departure
        Mixture distributions over arrival and departure hour.
    charger_kw
        Charger rating drawn by each present vehicle, in kilowatts.
    """

    name: str
    fleet_size: int
    arrival: Mixture
    departure: Mixture
    charger_kw: float


# Defining the data classes before importing the withheld modules matters: the
# fitted-parameter module builds CategorySpec instances, so it imports the names
# above while this module is still initialising.
try:
    from ._engine import build_mixture_pdf, simulate_occupancy
    from ._params import default_fleet

    ENGINE_AVAILABLE = True
except Exception:
    ENGINE_AVAILABLE = False

    def _withheld(*_args, **_kwargs):
        raise RuntimeError(
            "The charging-demand generation engine and its fitted parameters are "
            "withheld from the public release of this repository. The committed "
            "notebook shows the load curve they produce; the implementation is "
            "available on request."
        )

    build_mixture_pdf = simulate_occupancy = default_fleet = _withheld


def _mixture_from_records(records: list[dict]) -> Mixture:
    return Mixture(tuple(MixtureComponent(**record) for record in records))


def load_fleet_config(path: str | Path) -> list[CategorySpec]:
    """Build a fleet from a YAML config such as ``config/profiles.example.yaml``.

    The example config carries placeholder parameters; the fitted parameters
    behind the published results are withheld. This loader lets a fleet be
    described entirely in configuration without touching code.
    """
    config = yaml.safe_load(Path(path).read_text())
    charger_kw = float(config["charger_kw"])
    return [
        CategorySpec(
            name=category["name"],
            fleet_size=int(category["fleet_size"]),
            arrival=_mixture_from_records(category["arrival"]),
            departure=_mixture_from_records(category["departure"]),
            charger_kw=charger_kw,
        )
        for category in config["categories"]
    ]


def build_demand_profile(
    specs: list[CategorySpec],
    time_grid: np.ndarray = TIME_GRID,
    seed: int = 0,
) -> pd.DataFrame:
    """Simulate occupancy and charging load over the day for a fleet.

    Parameters
    ----------
    specs
        The behavioural categories making up the fleet.
    time_grid
        Hour-of-day grid; defaults to six-minute resolution over 24 hours.
    seed
        Seed for the random generator, for reproducible profiles.

    Returns
    -------
    pandas.DataFrame
        Columns ``hour``, then per category ``count_<name>`` and
        ``load_<name>_kw``, and finally ``load_total_kw``.
    """
    rng = np.random.default_rng(seed)
    profile = pd.DataFrame({"hour": time_grid})

    for spec in specs:
        arrival_pdf = build_mixture_pdf(spec.arrival, time_grid)
        departure_pdf = build_mixture_pdf(spec.departure, time_grid)
        occupancy = simulate_occupancy(time_grid, arrival_pdf, departure_pdf, spec.fleet_size, rng)
        profile[f"count_{spec.name}"] = occupancy
        profile[f"load_{spec.name}_kw"] = spec.charger_kw * occupancy

    load_columns = [column for column in profile.columns if column.startswith("load_")]
    profile["load_total_kw"] = profile[load_columns].sum(axis=1)
    return profile

"""Typed configuration loader over ``config/default.yaml``.

Every tunable in the simulation lives in the YAML file and is surfaced here as
a frozen dataclass, so downstream code gets attribute access, type checking and
a single source of truth for the electrical parameters, the grid reference and
the integration settings.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = REPO_ROOT / "config" / "default.yaml"


@dataclass(frozen=True)
class GridConfig:
    """The grid reference the loop synchronises to."""

    frequency: float
    reference_amplitude: float


@dataclass(frozen=True)
class BoostConfig:
    """Boost (step-up) converter electrical parameters."""

    inductance: float
    capacitance: float
    load_resistance: float
    switching_frequency: float
    duty: float
    input_voltage: float


@dataclass(frozen=True)
class ModulatorConfig:
    """Sinusoidal pulse-width modulator settings."""

    base_frequency: float
    pulses_per_half_cycle: int


@dataclass(frozen=True)
class FilterConfig:
    """Output low-pass filter; the resistance is designed from the corner."""

    capacitance: float
    corner_frequency: float


@dataclass(frozen=True)
class PllConfig:
    """Analogue phase-locked loop parameters."""

    capacitance: float
    peak_resistance: float
    peak_capacitance: float
    comparator_gain: float


@dataclass(frozen=True)
class PowerConfig:
    """Apparent-power operating point into the inductive grid tie."""

    active_power: float
    reactive_power: float
    tie_inductance: float
    grid_amplitude: float


@dataclass(frozen=True)
class SimulationConfig:
    """Integration horizon, step and the settled-window fraction."""

    start_time: float
    duration: float
    timestep: float
    settle_fraction: float


@dataclass(frozen=True)
class PathsConfig:
    """Project directories, resolved against the repository root."""

    artifacts: Path
    figures: Path


@dataclass(frozen=True)
class Config:
    """Full simulation configuration."""

    grid: GridConfig
    boost: BoostConfig
    modulator: ModulatorConfig
    filter: FilterConfig
    pll: PllConfig
    power: PowerConfig
    simulation: SimulationConfig
    paths: PathsConfig
    repo_root: Path = field(default=REPO_ROOT)


def load_config(path: str | Path | None = None) -> Config:
    """Load the YAML configuration into typed dataclasses.

    Parameters
    ----------
    path
        Location of the YAML file. Defaults to ``config/default.yaml`` at the
        repository root.

    Returns
    -------
    Config
        The fully typed configuration.
    """
    config_path = Path(path) if path is not None else DEFAULT_CONFIG_PATH
    raw = yaml.safe_load(config_path.read_text())
    root = config_path.resolve().parents[1]

    paths = PathsConfig(**{key: root / value for key, value in raw["paths"].items()})
    return Config(
        grid=GridConfig(
            frequency=float(raw["grid"]["frequency"]),
            reference_amplitude=float(raw["grid"]["reference_amplitude"]),
        ),
        boost=BoostConfig(
            inductance=float(raw["boost"]["inductance"]),
            capacitance=float(raw["boost"]["capacitance"]),
            load_resistance=float(raw["boost"]["load_resistance"]),
            switching_frequency=float(raw["boost"]["switching_frequency"]),
            duty=float(raw["boost"]["duty"]),
            input_voltage=float(raw["boost"]["input_voltage"]),
        ),
        modulator=ModulatorConfig(
            base_frequency=float(raw["modulator"]["base_frequency"]),
            pulses_per_half_cycle=int(raw["modulator"]["pulses_per_half_cycle"]),
        ),
        filter=FilterConfig(
            capacitance=float(raw["filter"]["capacitance"]),
            corner_frequency=float(raw["filter"]["corner_frequency"]),
        ),
        pll=PllConfig(
            capacitance=float(raw["pll"]["capacitance"]),
            peak_resistance=float(raw["pll"]["peak_resistance"]),
            peak_capacitance=float(raw["pll"]["peak_capacitance"]),
            comparator_gain=float(raw["pll"]["comparator_gain"]),
        ),
        power=PowerConfig(
            active_power=float(raw["power"]["active_power"]),
            reactive_power=float(raw["power"]["reactive_power"]),
            tie_inductance=float(raw["power"]["tie_inductance"]),
            grid_amplitude=float(raw["power"]["grid_amplitude"]),
        ),
        simulation=SimulationConfig(
            start_time=float(raw["simulation"]["start_time"]),
            duration=float(raw["simulation"]["duration"]),
            timestep=float(raw["simulation"]["timestep"]),
            settle_fraction=float(raw["simulation"]["settle_fraction"]),
        ),
        paths=paths,
        repo_root=root,
    )

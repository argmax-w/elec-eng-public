"""Configuration loader checks."""

from invertermodel.config import (
    BoostConfig,
    Config,
    PllConfig,
    load_config,
)


def test_default_config_loads_and_is_typed():
    cfg = load_config()
    assert isinstance(cfg, Config)
    assert isinstance(cfg.boost, BoostConfig)
    assert isinstance(cfg.pll, PllConfig)
    assert cfg.grid.frequency == 50.0
    assert cfg.boost.input_voltage == 2.5
    assert cfg.modulator.pulses_per_half_cycle == 25
    assert isinstance(cfg.modulator.pulses_per_half_cycle, int)


def test_paths_are_absolute_and_named():
    cfg = load_config()
    assert cfg.paths.artifacts.name == "artifacts"
    assert cfg.paths.figures.name == "figures"
    assert cfg.paths.artifacts.is_absolute()
    assert cfg.paths.figures.is_absolute()


def test_simulation_block_is_positive():
    cfg = load_config()
    assert cfg.simulation.duration > 0.0
    assert cfg.simulation.timestep > 0.0
    assert 0.0 < cfg.simulation.settle_fraction < 1.0

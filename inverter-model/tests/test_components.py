"""Component and simulation checks: step-up, lock and finite outputs."""

from dataclasses import replace

import numpy as np
from invertermodel.components import BoostConverter, OutputFilter
from invertermodel.config import load_config
from invertermodel.power import power_settings
from invertermodel.simulation import simulate


def test_boost_converter_steps_voltage_up():
    cfg = load_config().boost
    converter = BoostConverter(
        inductance=cfg.inductance,
        capacitance=cfg.capacitance,
        switching_frequency=cfg.switching_frequency,
        duty=cfg.duty,
        input_voltage=cfg.input_voltage,
        load_resistance=cfg.load_resistance,
    )
    dt = 1.0e-7
    for step in range(1, 200_001):
        converter.step(step * dt)
    # A boost converter raises the output above its input.
    assert converter.capacitor_voltage > cfg.input_voltage
    assert np.isfinite(converter.capacitor_voltage)


def test_output_filter_corner_sets_resistance():
    output_filter = OutputFilter(capacitance=2.0e-6, corner_frequency=50.5)
    expected = 1.0 / (2 * np.pi * 50.5 * 2.0e-6)
    assert np.isclose(output_filter.resistance, expected)


def test_output_filter_tracks_constant_input():
    output_filter = OutputFilter(capacitance=2.0e-6, corner_frequency=50.5)
    dt = 1.0e-5
    for step in range(1, 2001):
        output_filter.step(step * dt, voltage_in=1.0)
    # A first-order low pass driven by a step rises towards the input level.
    assert 0.0 < output_filter.v_out < 1.0
    assert output_filter.v_out > 0.5


def test_power_settings_returns_sane_magnitudes():
    point = power_settings(p=1.0, q=0.3, tie_inductance=1.0e-3, grid_amplitude=1.0)
    # |S| = sqrt(P^2 + Q^2); current magnitude is |S| / V.
    assert np.isclose(point.current_magnitude, np.hypot(1.0, 0.3))
    # A small tie reactance leaves the inverter voltage close to the grid.
    assert np.isclose(point.inverter_magnitude, 1.0, atol=0.05)
    assert point.inverter_angle > 0.0


def test_simulation_runs_and_locks_on_short_horizon():
    base = load_config()
    cfg = replace(base, simulation=replace(base.simulation, duration=0.05))
    result = simulate(cfg)

    for array in (
        result.boost_voltage,
        result.pwm_voltage,
        result.filtered_voltage,
        result.reference,
        result.phase_error,
    ):
        assert array.shape == result.time.shape
        assert np.isfinite(array).all()

    # The boost stage steps the input voltage up.
    assert result.boost_voltage[-1] > base.boost.input_voltage

    # The phase-error ripple narrows as the loop pulls into step.
    transient = result.phase_error[: result.settle_index]
    locked = result.phase_error[result.settle_index :]
    assert locked.std() < transient.std()

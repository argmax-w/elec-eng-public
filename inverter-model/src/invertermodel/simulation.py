"""The cascade simulation loop and its recorded time series.

The four stages are stepped in order on a fixed time grid: the boost converter
sets the DC link, the modulator chops it into a sinusoidal-PWM waveform under
the loop's frequency correction, the output filter smooths it and the
phase-locked loop compares the result against the grid reference to form the
correction used on the next step. Every quantity worth plotting is recorded and
returned as a dense array.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .components import BoostConverter, OutputFilter, PhaseLockedLoop, PwmModulator
from .config import Config


@dataclass(frozen=True)
class SimulationResult:
    """Recorded time series from a simulation run.

    All arrays share the ``time`` grid. The ``settled`` slice marks the tail of
    the record treated as locked steady state, for spectra and lock metrics.
    """

    time: np.ndarray
    boost_voltage: np.ndarray
    pwm_voltage: np.ndarray
    filtered_voltage: np.ndarray
    reference: np.ndarray
    phase_error: np.ndarray
    settle_index: int

    @property
    def settled(self) -> slice:
        """Slice selecting the settled tail of the record."""
        return slice(self.settle_index, None)


def simulate(cfg: Config) -> SimulationResult:
    """Run the cascaded inverter simulation under a configuration.

    Parameters
    ----------
    cfg
        Full configuration; the ``simulation`` block sets the time grid and the
        component blocks set the electrical parameters.

    Returns
    -------
    SimulationResult
        Time and the recorded boost, PWM, filtered, reference and phase-error
        series, with the settled-window index.
    """
    boost = BoostConverter(
        inductance=cfg.boost.inductance,
        capacitance=cfg.boost.capacitance,
        switching_frequency=cfg.boost.switching_frequency,
        duty=cfg.boost.duty,
        input_voltage=cfg.boost.input_voltage,
        load_resistance=cfg.boost.load_resistance,
    )
    modulator = PwmModulator(
        base_frequency=cfg.modulator.base_frequency,
        pulses_per_half_cycle=cfg.modulator.pulses_per_half_cycle,
    )
    output_filter = OutputFilter(
        capacitance=cfg.filter.capacitance,
        corner_frequency=cfg.filter.corner_frequency,
    )
    pll = PhaseLockedLoop(
        capacitance=cfg.pll.capacitance,
        peak_resistance=cfg.pll.peak_resistance,
        peak_capacitance=cfg.pll.peak_capacitance,
        comparator_gain=cfg.pll.comparator_gain,
    )

    times = np.arange(
        cfg.simulation.start_time,
        cfg.simulation.start_time + cfg.simulation.duration,
        cfg.simulation.timestep,
    )
    n = times.size

    boost_voltage = np.empty(n)
    pwm_voltage = np.empty(n)
    filtered_voltage = np.empty(n)
    reference = np.empty(n)
    phase_error = np.empty(n)

    omega = 2 * np.pi * cfg.grid.frequency
    amplitude = cfg.grid.reference_amplitude
    phase_error_gain = 0.0

    for i, time in enumerate(times):
        boost.step(time)
        modulator.step(time, boost.capacitor_voltage, phase_error_gain)
        output_filter.step(time, modulator.voltage_out)

        grid_reference = amplitude * np.sin(omega * time)
        pll.step(time, grid_reference, output_filter.v_out)
        phase_error_gain = pll.phase_error_gain

        boost_voltage[i] = boost.capacitor_voltage
        pwm_voltage[i] = modulator.voltage_out
        filtered_voltage[i] = output_filter.v_out
        reference[i] = grid_reference
        phase_error[i] = pll.phase_error

    settle_index = int(cfg.simulation.settle_fraction * n)
    return SimulationResult(
        time=times,
        boost_voltage=boost_voltage,
        pwm_voltage=pwm_voltage,
        filtered_voltage=filtered_voltage,
        reference=reference,
        phase_error=phase_error,
        settle_index=settle_index,
    )

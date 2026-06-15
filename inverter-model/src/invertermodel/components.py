"""The four cascaded stages of the grid-following inverter.

Each stage is a small stateful object that the simulation loop steps once per
integration step. Each holds its own electrical state and advances it with an
explicit Euler update, using the textbook circuit relations rather than a
packaged solver so the switching and loop dynamics stay visible.

The cascade is boost converter -> sinusoidal PWM -> output filter ->
phase-locked loop, with the loop's phase error fed back into the modulator on
the next step.
"""

from __future__ import annotations

import numpy as np


class BoostConverter:
    """Boost (step-up) DC-DC converter with hard PWM switching.

    The converter alternates between two topologies at the switching frequency.
    With the switch closed the inductor charges from the input while the output
    capacitor discharges into the load; with the switch open the inductor drives
    the capacitor and load through the diode. The duty cycle sets the fraction
    of each period spent in the closed state and therefore the voltage step-up.
    """

    def __init__(
        self,
        inductance: float,
        capacitance: float,
        switching_frequency: float,
        duty: float,
        input_voltage: float,
        load_resistance: float,
    ) -> None:
        self.switching_frequency = switching_frequency
        self.period = 1.0 / switching_frequency
        self.duty = duty

        self.load_resistance = load_resistance
        self.inductance = inductance
        self.capacitance = capacitance
        self.input_voltage = input_voltage

        self.inductor_current = 0.0
        self.inductor_voltage = 0.0
        self.capacitor_voltage = 0.0

        self.switch_closed = True
        self.prev_time = 0.0
        self.time_in_state = 0.0

    def step(self, time: float) -> None:
        """Advance the converter to ``time`` and update its state."""
        time_diff = time - self.prev_time
        self.time_in_state += time_diff

        # Toggle the switch once it has held its current state for the share of
        # the period set by the duty cycle.
        closed_hold = self.time_in_state >= self.period * self.duty
        open_hold = self.time_in_state >= self.period * (1.0 - self.duty)
        if (closed_hold and self.switch_closed) or (open_hold and not self.switch_closed):
            self.switch_closed = not self.switch_closed
            self.time_in_state = 0.0

        if self.switch_closed:
            # The two storage elements are decoupled: the inductor charges from
            # the input and the capacitor discharges into the load.
            self.inductor_voltage = self.input_voltage
            self.inductor_current += time_diff * self.inductor_voltage / self.inductance
            load_time_constant = self.load_resistance * self.capacitance
            self.capacitor_voltage += -time_diff * self.capacitor_voltage / load_time_constant
        else:
            # The switch is open and the converter is a coupled second-order
            # circuit; integrate its state-space form one step.
            state_matrix = np.array(
                [
                    [0.0, -1.0 / self.inductance],
                    [1.0 / self.capacitance, -1.0 / (self.load_resistance * self.capacitance)],
                ]
            )
            state = np.array([self.inductor_current, self.capacitor_voltage])
            forcing = np.array([self.input_voltage / self.inductance, 0.0])
            derivative = state_matrix @ state + forcing

            self.inductor_voltage = self.input_voltage - self.capacitor_voltage
            self.inductor_current += derivative[0] * time_diff
            self.capacitor_voltage += derivative[1] * time_diff

        self.prev_time = time


class PwmModulator:
    """Sinusoidal pulse-width modulator driving an H-bridge.

    The modulator chops the boost-converter output into pulses whose width
    tracks a sine reference, producing a switched approximation of a mains-
    frequency sinusoid. The four switch signals ``d1``..``d4`` select the bridge
    diagonal that applies the input voltage with the sign of the reference. The
    phase-error input from the loop trims the output frequency, pulling the
    inverter into step with the grid.
    """

    def __init__(self, base_frequency: float, pulses_per_half_cycle: int) -> None:
        self.base_frequency = base_frequency
        self.frequency = base_frequency
        self.period = 1.0 / base_frequency

        self.pulses_per_half_cycle = pulses_per_half_cycle
        self.pulse_width = self.period / (2 * pulses_per_half_cycle)

        self.time_in_period = 0.0
        self.elapsed_time = 0.0
        self.prev_time = 0.0

        self.voltage_out = 0.0
        self.width_modulator = 0.0
        self.value = 0
        self.d1 = 0
        self.d2 = 0
        self.d3 = 0
        self.d4 = 0

    def step(self, time: float, voltage_in: float, phase_error: float) -> None:
        """Advance the modulator one step with the latest loop phase error."""
        self.voltage_in = voltage_in

        time_diff = time - self.prev_time
        self.time_in_period += time_diff
        self.elapsed_time += time_diff

        # The loop phase error nudges the output frequency, and with it the
        # pulse width, so the modulated waveform can be pulled into step.
        self.frequency = self.base_frequency + phase_error
        self.period = 1.0 / self.frequency
        self.pulse_width = self.period / (2 * self.pulses_per_half_cycle)

        modulated_width = self.pulse_width * np.abs(self.width_modulator)

        # A pulse is on for the modulated fraction of the slot; its sign follows
        # the sine reference so the bridge reproduces both half cycles.
        if self.time_in_period <= modulated_width:
            self.value = int(np.sign(self.width_modulator))
        else:
            self.value = 0

        if self.value == 1:
            self.d1, self.d2, self.d3, self.d4 = 1, 1, 0, 0
            self.voltage_out = self.voltage_in
        elif self.value == -1:
            self.d1, self.d2, self.d3, self.d4 = 0, 0, 1, 1
            self.voltage_out = -self.voltage_in
        else:
            self.d1, self.d2, self.d3, self.d4 = 0, 0, 0, 0
            self.voltage_out = 0.0

        # At the end of each slot, resample the sine reference for the next one.
        if self.time_in_period >= self.pulse_width:
            self.width_modulator = np.sin(2 * np.pi * self.frequency * self.elapsed_time)
            self.time_in_period = 0.0

        self.prev_time = time


class OutputFilter:
    """First-order RC low-pass filter on the modulator output.

    The resistance is designed from the capacitance so the corner frequency
    sits just above the mains line, passing the synthesised sinusoid and
    rejecting the switching ripple. The filter integrates its single state, the
    output voltage, with an explicit Euler step.
    """

    def __init__(self, capacitance: float, corner_frequency: float) -> None:
        self.capacitance = capacitance
        self.resistance = 1.0 / (2 * np.pi * corner_frequency * capacitance)
        self.v_out = 0.0
        self.prev_time = 0.0

    def step(self, time: float, voltage_in: float) -> None:
        """Advance the filter one step with the modulator output."""
        time_diff = time - self.prev_time
        self.prev_time = time

        self.v_in = voltage_in
        time_constant = self.resistance * self.capacitance
        self.v_out += (self.v_in - self.v_out) / time_constant * time_diff


class PhaseLockedLoop:
    """Analogue phase-locked loop synchronising the inverter to the grid.

    Two peak detectors recover the envelopes of the grid reference and the
    filtered inverter output; a phase comparator forms an error from their
    product and the reference derivative, and a loop filter smooths it. The
    scaled error is the correction fed back to the modulator. When locked the
    error settles to a small constant, the steady phase offset that sustains
    synchronism.
    """

    def __init__(
        self,
        capacitance: float,
        peak_resistance: float,
        peak_capacitance: float,
        comparator_gain: float,
    ) -> None:
        self.capacitance = capacitance
        self.resistance = 1.0 / (np.pi * capacitance)
        self.peak_resistance = peak_resistance
        self.peak_capacitance = peak_capacitance
        self.comparator_gain = comparator_gain

        self.prev_v1_in = 0.0
        self.filtered_v_out = 0.0
        self.prev_time = 0.0
        self.phase_error = 0.0
        self.phase_error_gain = 0.0
        self.v_out = 0.0

        self.v_c1 = 0.0
        self.i_c1 = 0.0
        self.v_r1 = 0.0
        self.v_c2 = 0.0
        self.i_c2 = 0.0
        self.v_r2 = 0.0
        self.last_peak_v_c1 = 0.0
        self.last_peak_v_c2 = 0.0
        self.discharge_time_1 = 0.0
        self.discharge_time_2 = 0.0

    def _peak_detect(
        self,
        voltage_in: float,
        v_c: float,
        last_peak: float,
        discharge_time: float,
        time_diff: float,
    ) -> tuple[float, float, float, float, float]:
        """One peak-detector update: charge to a new peak or decay from the last."""
        magnitude = np.abs(voltage_in)
        if magnitude > v_c:
            # Rising input: the capacitor follows it to a new peak.
            i_c = -self.peak_capacitance * (v_c - magnitude) / time_diff
            v_c = v_c + i_c * time_diff / self.peak_capacitance
            v_r = magnitude
            return v_c, i_c, v_r, v_c, 0.0
        # Falling input: the peak is held and decays through the resistor.
        time_constant = self.peak_resistance * self.peak_capacitance
        v_c = last_peak * np.exp(-discharge_time / time_constant)
        v_r = v_c
        i_c = -(v_r / self.peak_resistance)
        return v_c, i_c, v_r, last_peak, discharge_time + time_diff

    def step(self, time: float, v1_in: float, v2_in: float) -> None:
        """Advance the loop with the grid reference and the inverter output."""
        time_diff = time - self.prev_time
        self.prev_time = time

        # Recover the envelopes of both inputs with peak detectors.
        self.v_c1, self.i_c1, self.v_r1, self.last_peak_v_c1, self.discharge_time_1 = (
            self._peak_detect(
                v1_in, self.v_c1, self.last_peak_v_c1, self.discharge_time_1, time_diff
            )
        )
        self.v_c2, self.i_c2, self.v_r2, self.last_peak_v_c2, self.discharge_time_2 = (
            self._peak_detect(
                v2_in, self.v_c2, self.last_peak_v_c2, self.discharge_time_2, time_diff
            )
        )

        # Phase comparator: the reference derivative against the second input,
        # normalised by the recovered envelopes.
        d_v1_in = (v1_in - self.prev_v1_in) / time_diff
        denom = self.v_r1 * self.v_r2
        if denom == 0:
            denom = 1.0
        self.v_out = 2.0 * (-d_v1_in * v2_in) / denom

        # Loop filter and gain stage to the modulator correction.
        time_constant = self.resistance * self.capacitance
        self.filtered_v_out += (self.v_out - self.filtered_v_out) / time_constant * time_diff
        self.phase_error = self.filtered_v_out
        self.phase_error_gain = self.phase_error * self.comparator_gain

        self.prev_v1_in = v1_in

# Model notes

This note is the engineering underneath the simulation: the control
architecture, the state-update equations for each of the four stages, the
parameters, and how the integration step was chosen so the model both resolves
the carrier and still finishes quickly. The inverter is single-phase and
grid-following, four stages cascaded and integrated on a fixed time grid, with a
closed loop synchronising the output to a 50 Hz grid reference.

## Control architecture

A feedforward chain closed by a single feedback term:

```
dc source --> boost converter --> sinusoidal PWM --> output filter --> grid tie
                                        ^                   |
                                        |                   v
                                  phase error <----- phase-locked loop <--- grid reference
```

Each step advances the four stages in order. The boost converter sets the
dc-link voltage. The modulator chops that link into a sinusoidal-PWM waveform,
its frequency trimmed by the loop's phase error from the previous step. The
output filter recovers the sinusoid. The PLL compares the recovered sinusoid
against the grid reference and produces the phase error used on the next step.
That scalar correction is the only feedback in the system, and it is what pulls
the free-running modulator into step with the grid.

## Stage equations

All updates are explicit (forward Euler) with step `dt = t_k - t_{k-1}`.

### Boost converter

A step-up DC-DC converter switched at the carrier frequency `f_sw` with duty
`D`. The switch toggles once it has held its state for the duty share of the
period. With the switch **closed** the inductor and output capacitor are
decoupled,

```
v_L = V_in
i_L <- i_L + dt * v_L / L
v_C <- v_C - dt * v_C / (R L_oad C)
```

and with the switch **open** the circuit is a coupled second-order system
integrated from its state-space form,

```
d/dt [i_L; v_C] = [[0, -1/L], [1/C, -1/(R C)]] [i_L; v_C] + [V_in/L; 0]
v_L = V_in - v_C.
```

Holding the switch closed for half of each period drives the link to roughly
twice the source.

### Sinusoidal pulse-width modulator

An H-bridge driven by a sinusoidal reference. Each carrier slot the reference
`m = sin(2 pi f t)` sets a modulated pulse width `PW * |m|`. The bridge applies
`+V_link`, `0` or `-V_link` by the sign of `m`, through the four switch signals
`d1..d4`. The loop phase error `e` trims the output frequency,

```
f <- f_base + e,
```

and that single line is the mechanism by which the modulated waveform is pulled
into phase.

### Output filter

A first-order RC low pass on the bridge output. The resistance is designed from
the capacitance so the corner sits just above the mains line,

```
R = 1 / (2 pi f_c C),   f_c ~ 50.5 Hz,
v_out <- v_out + dt * (v_in - v_out) / (R C).
```

The corner passes the 50 Hz sinusoid and rejects the carrier ripple above it.

### Analogue phase-locked loop

This is where the synchronisation happens. Two peak detectors recover the
envelopes of the grid reference and the filtered output. Each detector charges
its hold capacitor to a new peak when the input rises and otherwise decays it
through the discharge resistor,

```
rising:  v_C <- |v_in|
falling: v_C <- v_peak * exp(-t_discharge / (R_p C_p)).
```

A phase comparator forms an error from the reference derivative against the
filtered output, normalised by the envelopes,

```
v_err = 2 * (-d(v_ref)/dt * v_out) / (env_ref * env_out),
```

a loop filter smooths it, and a comparator gain scales it to the modulator
correction,

```
e_filt <- e_filt + dt * (v_err - e_filt) / (R C),
e = gain * e_filt,   gain = 0.05.
```

Once locked, `e` settles to a small steady value with a narrow ripple band: the
constant correction that holds synchronism.

## Parameters

Every parameter the model takes, with its default:

| Stage | Parameter | Symbol | Default |
| --- | --- | --- | --- |
| Grid | reference frequency | f | 50 Hz |
| Grid | reference amplitude | V_ref | 1 V |
| Boost | inductance | L | 2 uH |
| Boost | capacitance | C | 47 uF |
| Boost | load resistance | R | 2 ohm |
| Boost | switching frequency | f_sw | 2 MHz |
| Boost | duty | D | 0.5 |
| Boost | input voltage | V_in | 2.5 V |
| Modulator | base frequency | f_base | 50 Hz |
| Modulator | pulses per half cycle | PN | 25 |
| Filter | capacitance | C_f | 2 uF |
| Filter | corner frequency | f_c | 50.5 Hz |
| PLL | loop capacitance | C_l | 2 uF |
| PLL | peak-detector resistance | R_p | 10 kohm |
| PLL | peak-detector capacitance | C_p | 50 uF |
| PLL | comparator gain | k | 0.05 |
| Power | active power | P | 1 pu |
| Power | reactive power | Q | 0.3 pu |
| Power | tie inductance | L_tie | 1 mH |
| Power | grid amplitude | V_g | 1 V |

The `power_settings` helper inverts the grid-tie relation to return the line
current and inverter terminal voltage for a requested apparent power
`|S| = sqrt(P^2 + Q^2)` into the inductive coupling, taking the grid voltage
phasor as the angle reference.

## Time resolution

The original exploratory model integrated from 1 us to 1.5 s at a 1 us step,
about 1.5 million iterations of the Python loop. Far too slow to ship as a
reproducible artefact. The horizon and step now live in `config/default.yaml`.
The default integrates 0.5 s at a 2e-7 s step (2.5 million steps). The step
still resolves the 2 MHz carrier, and half a second is long enough to show the
loop overshoot, decay and settle. The run finishes in under fifteen seconds, and
the phase-error ripple band narrows by roughly a factor of five between the
transient and locked windows. That narrowing is the lock criterion the notebook
reports.

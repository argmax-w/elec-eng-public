"""The Kuramoto model and the spectrum helper for the cicada recording.

A chorus of cicadas is modelled as ``N`` coupled phase oscillators, each with
its own natural frequency, pulled towards its neighbours through a sine
coupling:

    dtheta_i/dt = omega_i + (K / N) * sum_j sin(theta_j - theta_i).

Whether the population locks into a common rhythm is read from the complex
order parameter

    r e^{i psi} = (1 / N) sum_j e^{i theta_j},

whose magnitude ``|r|`` runs from 0 for a scattered population to 1 for perfect
synchrony. Above a critical coupling the population condenses and ``|r|`` rises
towards 1; below it the oscillators drift and ``|r|`` stays near zero.

The audio helper turns a field recording of the chorus into a magnitude
spectrum, so the dominant call frequency can be compared with the simulated
natural frequency.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
from numpy.typing import NDArray
from scipy.io import wavfile


@dataclass(frozen=True)
class KuramotoResult:
    """Output of a Kuramoto simulation.

    Attributes
    ----------
    times
        Time of each recorded step, seconds.
    phases
        Oscillator phases, shape ``(steps, N)``, wrapped to ``[0, 2 pi)``.
    natural_frequencies
        The angular natural frequency ``omega_i`` of each oscillator.
    coupling
        The coupling strength ``K`` used.
    """

    times: NDArray[np.float64]
    phases: NDArray[np.float64]
    natural_frequencies: NDArray[np.float64]
    coupling: float


def order_parameter(phases: NDArray[np.float64]) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Complex order parameter of a set of phases.

    Accepts a single snapshot (shape ``(N,)``) or a time history (shape
    ``(steps, N)``) and reduces over the oscillator axis.

    Returns
    -------
    tuple of numpy.ndarray
        The coherence ``|r|`` in ``[0, 1]`` and the mean phase ``psi`` in
        radians, each with the oscillator axis removed.
    """
    z = np.mean(np.exp(1j * phases), axis=-1)
    return np.abs(z), np.angle(z)


def simulate_kuramoto(
    n: int,
    coupling: float,
    *,
    natural_frequency: float = 2.0 * np.pi,
    frequency_spread: float = 0.0,
    steps: int = 3000,
    dt: float = 0.01,
    seed: int | None = None,
) -> KuramotoResult:
    """Simulate ``N`` coupled phase oscillators.

    Natural frequencies are drawn once from a normal distribution centred on
    ``natural_frequency`` with standard deviation ``frequency_spread``; a zero
    spread gives an identical-frequency population, the easiest to synchronise.
    Integration is explicit Euler, which is adequate here because the coupling
    is bounded and the step is small. The all-pairs coupling sum is formed with
    a broadcast outer difference, so each step is a single vectorised operation
    rather than a double loop over oscillators.

    Parameters
    ----------
    n
        Number of oscillators.
    coupling
        Coupling strength ``K``.
    natural_frequency
        Mean angular natural frequency, radians per second.
    frequency_spread
        Standard deviation of the natural frequencies, radians per second.
    steps
        Number of integration steps to record.
    dt
        Time step, seconds.
    seed
        Seed for the initial phases and the natural-frequency draw.

    Returns
    -------
    KuramotoResult
        Times, the phase history and the population parameters.
    """
    rng = np.random.default_rng(seed)
    omega = rng.normal(natural_frequency, frequency_spread, size=n)
    theta = rng.uniform(0.0, 2.0 * np.pi, size=n)

    phases = np.empty((steps, n), dtype=np.float64)
    scale = coupling / n
    for step in range(steps):
        phases[step] = theta
        # All-pairs phase differences via broadcasting: row i holds
        # theta_j - theta_i across j, summed to give each oscillator's pull.
        coupling_term = scale * np.sin(theta[None, :] - theta[:, None]).sum(axis=1)
        theta = (theta + dt * (omega + coupling_term)) % (2.0 * np.pi)

    times = np.arange(steps) * dt
    return KuramotoResult(
        times=times,
        phases=phases,
        natural_frequencies=omega,
        coupling=coupling,
    )


@dataclass(frozen=True)
class Spectrum:
    """A magnitude spectrum and its binned summary.

    Attributes
    ----------
    frequency
        Frequencies of the real FFT, hertz.
    magnitude
        Magnitude at each frequency.
    bin_frequency
        Centre frequency of each bin, hertz.
    bin_magnitude
        Mean magnitude within each bin.
    sample_rate
        Sample rate of the source recording, hertz.
    duration
        Length of the recording, seconds.
    """

    frequency: NDArray[np.float64]
    magnitude: NDArray[np.float64]
    bin_frequency: NDArray[np.float64]
    bin_magnitude: NDArray[np.float64]
    sample_rate: int
    duration: float

    @property
    def dominant_frequency(self) -> float:
        """Frequency of the largest spectral peak above DC, hertz."""
        non_dc = self.frequency > 0
        idx = np.argmax(self.magnitude[non_dc])
        return float(self.frequency[non_dc][idx])


def audio_spectrum(path: str | Path, *, bin_width: float = 100.0) -> Spectrum:
    """Magnitude spectrum of a WAV recording, with a binned summary.

    The signal is reduced to mono if stereo, then transformed with a real FFT.
    The magnitude spectrum is averaged into bins of ``bin_width`` hertz to give
    a coarse view of where the chorus energy sits.

    Parameters
    ----------
    path
        Path to a WAV file.
    bin_width
        Width of the frequency bins, hertz.

    Returns
    -------
    Spectrum
        The full and binned magnitude spectra with recording metadata.

    Raises
    ------
    FileNotFoundError
        If the recording is absent. The recording is a large field capture
        that is not committed, so callers should guard for this and degrade
        gracefully.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(
            f"audio recording not found at {path}; supply a WAV file as described "
            "in data/README.md to run the spectrum"
        )
    sample_rate, amplitude = wavfile.read(path)
    amplitude = np.asarray(amplitude, dtype=np.float64)
    if amplitude.ndim > 1:
        amplitude = amplitude.mean(axis=1)

    n = len(amplitude)
    frequency = np.fft.rfftfreq(n, d=1.0 / sample_rate)
    magnitude = np.abs(np.fft.rfft(amplitude))

    bins = np.round(frequency / bin_width) * bin_width
    edges = np.unique(bins)
    bin_magnitude = np.array([magnitude[bins == edge].mean() for edge in edges])

    return Spectrum(
        frequency=frequency,
        magnitude=magnitude,
        bin_frequency=edges,
        bin_magnitude=bin_magnitude,
        sample_rate=int(sample_rate),
        duration=n / sample_rate,
    )

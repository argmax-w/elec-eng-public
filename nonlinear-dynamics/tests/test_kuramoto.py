"""Kuramoto checks: the order parameter is bounded and rises under coupling."""

import numpy as np
from nldynamics.kuramoto import order_parameter, simulate_kuramoto


def test_order_parameter_bounds():
    rng = np.random.default_rng(0)
    phases = rng.uniform(0, 2 * np.pi, size=(40, 25))
    coherence, mean_phase = order_parameter(phases)
    assert coherence.shape == (40,)
    assert np.all((coherence >= 0.0) & (coherence <= 1.0))
    assert np.all((mean_phase >= -np.pi) & (mean_phase <= np.pi))


def test_aligned_phases_give_unit_coherence():
    phases = np.full((1, 16), 0.7)
    coherence, _ = order_parameter(phases)
    np.testing.assert_allclose(coherence, 1.0)


def test_scattered_phases_give_low_coherence():
    # Phases spread evenly round the circle cancel out.
    phases = np.linspace(0, 2 * np.pi, 100, endpoint=False)[None, :]
    coherence, _ = order_parameter(phases)
    assert coherence[0] < 1e-10


def test_strong_coupling_identical_frequencies_synchronises():
    # Identical natural frequencies and strong coupling: the population locks.
    result = simulate_kuramoto(
        n=30,
        coupling=4.0,
        frequency_spread=0.0,
        steps=2000,
        dt=0.01,
        seed=1,
    )
    coherence, _ = order_parameter(result.phases)
    assert coherence[0] < 0.6  # scattered start
    assert coherence[-200:].mean() > 0.95  # synchronised finish


def test_zero_coupling_stays_incoherent():
    # Without coupling and with spread frequencies, phases keep drifting apart.
    result = simulate_kuramoto(
        n=40,
        coupling=0.0,
        frequency_spread=0.8,
        steps=2000,
        dt=0.01,
        seed=2,
    )
    coherence, _ = order_parameter(result.phases)
    assert coherence[-200:].mean() < 0.5

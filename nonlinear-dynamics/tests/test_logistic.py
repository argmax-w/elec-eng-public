"""Logistic-map checks: fixed points and the sign of the Lyapunov exponent."""

import numpy as np
from nldynamics.logistic import (
    bifurcation,
    cobweb,
    iterate,
    logistic_map,
    lyapunov_exponent,
)


def test_zero_is_a_fixed_point():
    np.testing.assert_allclose(logistic_map(3.2, np.array([0.0])), 0.0)


def test_nontrivial_fixed_point():
    # The map has a fixed point at x* = 1 - 1/r for r > 1.
    r = 2.8
    x_star = 1.0 - 1.0 / r
    np.testing.assert_allclose(logistic_map(r, np.array([x_star])), x_star)


def test_iterate_converges_to_fixed_point_when_stable():
    r = 2.8
    trajectory = iterate(r, 0.2, n=50, discard=200)
    np.testing.assert_allclose(trajectory, 1.0 - 1.0 / r, atol=1e-6)


def test_cobweb_polyline_length():
    xs, ys = cobweb(3.5, 0.2, n=10)
    # The seed plus two vertices per iteration.
    assert len(xs) == len(ys) == 1 + 2 * 10


def test_lyapunov_negative_in_stable_window():
    # At r = 2.8 the map settles to a single fixed point: contraction.
    exponent = lyapunov_exponent(2.8)
    assert exponent < 0.0


def test_lyapunov_positive_in_chaotic_window():
    # At r = 3.9 the map is chaotic: nearby orbits diverge.
    exponent = lyapunov_exponent(3.9)
    assert exponent > 0.0


def test_lyapunov_vectorises_over_r():
    r = np.array([2.8, 3.9])
    exponents = lyapunov_exponent(r)
    assert exponents.shape == (2,)
    assert exponents[0] < 0.0 < exponents[1]


def test_bifurcation_returns_paired_points():
    r = np.linspace(2.5, 4.0, 200)
    last = 50
    r_points, x_points = bifurcation(r, iterations=300, last=last)
    assert r_points.shape == x_points.shape == (r.size * last,)
    assert np.all((x_points >= 0.0) & (x_points <= 1.0))


def test_bifurcation_period_one_window():
    # A single r in the stable regime collapses onto one attractor value.
    r = np.array([2.8])
    _, x_points = bifurcation(r, iterations=500, last=50)
    assert np.ptp(x_points) < 1e-6

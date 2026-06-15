"""The logistic map and the diagnostics built on it.

The map is

    x_{n+1} = r x_n (1 - x_n),

a single nonlinearity that still moves through fixed points, a period-doubling
cascade and chaos as the growth rate ``r`` is raised. The
routines here cover one trajectory, the geometric cobweb construction, the
bifurcation diagram swept over ``r`` and the Lyapunov exponent that separates
the stable windows from the chaotic ones.

The Lyapunov exponent uses the analytic derivative of the map. For the
logistic map ``f(x) = r x (1 - x)`` the derivative is ``f'(x) = r - 2 r x``,
so the exponent is the long-run average of ``log|r - 2 r x|`` along the orbit;
it is negative where nearby trajectories converge and positive where they
diverge exponentially.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray


def logistic_map(r: float | NDArray[np.float64], x: NDArray[np.float64]) -> NDArray[np.float64]:
    """One step of the logistic map ``r x (1 - x)``.

    Both arguments broadcast, so ``r`` may be a scalar with an array of states
    (a swept ensemble) or an array of states with a single ``r``.
    """
    return r * x * (1.0 - x)


def iterate(
    r: float,
    x0: float,
    n: int,
    *,
    discard: int = 0,
) -> NDArray[np.float64]:
    """Iterate the map from ``x0`` and return the trajectory.

    Parameters
    ----------
    r
        Growth rate.
    x0
        Initial state in ``[0, 1]``.
    n
        Number of points to keep.
    discard
        Transient iterations dropped before recording, so the returned series
        sits on the attractor rather than the approach to it.

    Returns
    -------
    numpy.ndarray
        The kept trajectory, length ``n``.
    """
    x = float(x0)
    for _ in range(discard):
        x = r * x * (1.0 - x)
    out = np.empty(n, dtype=np.float64)
    for i in range(n):
        out[i] = x
        x = r * x * (1.0 - x)
    return out


def cobweb(r: float, x0: float, n: int) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Vertices of the cobweb (staircase) construction.

    The cobweb plot traces the iteration geometrically: from ``(x, x)`` on the
    diagonal it steps vertically to the curve at ``(x, f(x))``, then
    horizontally back to the diagonal at ``(f(x), f(x))``, and repeats. The
    returned coordinate arrays are the polyline of those moves, ready to pass
    straight to a single ``plot`` call.

    Returns
    -------
    tuple of numpy.ndarray
        The ``x`` and ``y`` vertex sequences of the staircase.
    """
    xs = [x0]
    ys = [0.0]
    x = float(x0)
    for _ in range(n):
        y = r * x * (1.0 - x)
        xs.extend((x, y))
        ys.extend((y, y))
        x = y
    return np.asarray(xs), np.asarray(ys)


def bifurcation(
    r: NDArray[np.float64],
    *,
    iterations: int = 1000,
    last: int = 100,
    x0: float = 1e-5,
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Sweep ``r`` and collect the attractor of each map.

    Every value of ``r`` is iterated from the same seed; the first
    ``iterations - last`` steps are treated as transient and discarded, and the
    remaining ``last`` iterates are returned as the sampled attractor. The
    whole sweep advances as one vectorised ensemble, one map per value of
    ``r``, so the cost scales with the grid width rather than with a Python
    loop over it.

    Returns
    -------
    tuple of numpy.ndarray
        Flattened ``(r, x)`` pairs, one point per recorded iterate, suitable
        for a scatter of the bifurcation diagram.
    """
    r = np.asarray(r, dtype=np.float64)
    x = x0 * np.ones_like(r)
    transient = iterations - last
    r_points: list[NDArray[np.float64]] = []
    x_points: list[NDArray[np.float64]] = []
    for i in range(iterations):
        x = logistic_map(r, x)
        if i >= transient:
            r_points.append(r)
            x_points.append(x.copy())
    return np.concatenate(r_points), np.concatenate(x_points)


def lyapunov_exponent(
    r: float | NDArray[np.float64],
    *,
    iterations: int = 1000,
    discard: int = 100,
    x0: float = 1e-5,
) -> NDArray[np.float64]:
    """Lyapunov exponent of the logistic map at each ``r``.

    The exponent is the mean of ``log|f'(x)| = log|r - 2 r x|`` over the orbit,
    after a transient is discarded so the average is taken on the attractor.
    Negative values mark stable (periodic) windows where perturbations decay;
    positive values mark chaos, where they grow. ``r`` may be a scalar or an
    array, and the computation is vectorised across the array.

    Returns
    -------
    numpy.ndarray
        The exponent for each value of ``r`` (a zero-dimensional array for a
        scalar input).
    """
    r = np.asarray(r, dtype=np.float64)
    x = x0 * np.ones_like(r)
    for _ in range(discard):
        x = logistic_map(r, x)
    total = np.zeros_like(r)
    for _ in range(iterations):
        total += np.log(np.abs(r - 2.0 * r * x))
        x = logistic_map(r, x)
    return total / iterations

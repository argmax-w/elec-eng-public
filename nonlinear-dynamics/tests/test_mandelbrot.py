"""Mandelbrot checks: interior points stay, exterior points escape, shape holds."""

import numpy as np
from nldynamics.mandelbrot import ZOOMS, Region, escape_counts


def single_point_region(real: float, imag: float, max_iter: int) -> Region:
    """A one-pixel window centred on a single ``c`` for a pointwise test.

    The window is given a tiny but non-zero span so the aspect ratio is
    defined; with one pixel each side the grid samples exactly ``(real, imag)``.
    """
    eps = 1e-9
    return Region(
        min_real=real,
        max_real=real + eps,
        min_imag=imag,
        max_imag=imag + eps,
        width=1,
        max_iter=max_iter,
    )


def test_origin_is_in_the_set():
    # c = 0 has orbit fixed at 0, so it never escapes and hits the cap.
    counts = escape_counts(single_point_region(0.0, 0.0, max_iter=100))
    assert counts.shape == (1, 1)
    assert counts[0, 0] == 100


def test_known_interior_point_hits_max_iter():
    # c = -1 cycles between 0 and -1: bounded, so it reaches the cap.
    counts = escape_counts(single_point_region(-1.0, 0.0, max_iter=150))
    assert counts[0, 0] == 150


def test_exterior_point_escapes_quickly():
    # c = 2 escapes immediately; well outside the set.
    counts = escape_counts(single_point_region(2.0, 0.0, max_iter=100))
    assert counts[0, 0] < 5


def test_output_shape_matches_grid():
    region = Region(
        min_real=-2.0,
        max_real=0.5,
        min_imag=-1.2,
        max_imag=1.2,
        width=120,
        max_iter=80,
    )
    counts = escape_counts(region)
    assert counts.shape == (region.height, region.width)


def test_counts_are_bounded_by_max_iter():
    region = ZOOMS["full"]
    counts = escape_counts(region, max_iter=60)
    assert counts.min() >= 0
    assert counts.max() == 60


def test_max_iter_override_changes_interior_value():
    region = single_point_region(0.0, 0.0, max_iter=10)
    np.testing.assert_array_equal(escape_counts(region, max_iter=42), np.array([[42]]))

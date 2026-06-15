"""Escape-time rendering of the Mandelbrot set.

A point ``c`` belongs to the set if the iteration

    z_{n+1} = z_n^2 + c,    z_0 = 0,

stays bounded. A point is treated as escaped once ``|z| > 2``, beyond which the
orbit always diverges. The escape time colours the boundary; points that never
escape within ``max_iter`` count as inside.

The render is vectorised: one complex grid is advanced in lockstep and a
boolean mask retires pixels as they escape, so there is no per-pixel loop.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

ESCAPE_RADIUS = 2.0


@dataclass(frozen=True)
class Region:
    """A rectangular window of the complex plane to render.

    Parameters
    ----------
    min_real, max_real
        Real-axis bounds.
    min_imag, max_imag
        Imaginary-axis bounds.
    width
        Horizontal resolution in pixels; the vertical resolution is chosen to
        keep the pixels square for the given aspect ratio.
    max_iter
        Iteration cap used as the escape-time ceiling.
    name
        Short label, used for figure filenames.
    """

    min_real: float
    max_real: float
    min_imag: float
    max_imag: float
    width: int = 800
    max_iter: int = 200
    name: str = "region"

    @property
    def aspect(self) -> float:
        """Height-to-width ratio of the window in the plane."""
        return (self.max_imag - self.min_imag) / (self.max_real - self.min_real)

    @property
    def height(self) -> int:
        """Vertical resolution in pixels, chosen to keep pixels square."""
        return max(1, round(self.width * self.aspect))

    @property
    def extent(self) -> tuple[float, float, float, float]:
        """Bounds in matplotlib ``imshow`` order ``(left, right, bottom, top)``."""
        return (self.min_real, self.max_real, self.min_imag, self.max_imag)

    def grid(self) -> NDArray[np.complex128]:
        """The complex sampling grid, shape ``(height, width)``."""
        real = np.linspace(self.min_real, self.max_real, self.width)
        imag = np.linspace(self.min_imag, self.max_imag, self.height)
        return real[None, :] + 1j * imag[:, None]


def escape_counts(region: Region, max_iter: int | None = None) -> NDArray[np.int32]:
    """Escape-time counts for every pixel of ``region``.

    The grid is advanced as one array; a mask tracks which pixels are still
    bounded and the escape iteration is recorded the first step a pixel crosses
    the escape radius. Escaped pixels are frozen so they neither overflow nor
    re-enter the active set.

    Parameters
    ----------
    region
        The window to render.
    max_iter
        Iteration cap; defaults to ``region.max_iter``. Pixels that never
        escape are returned with this value, marking the interior of the set.

    Returns
    -------
    numpy.ndarray
        Integer escape counts of shape ``(region.height, region.width)``.
    """
    cap = region.max_iter if max_iter is None else max_iter
    c = region.grid()
    z = np.zeros_like(c)
    counts = np.full(c.shape, cap, dtype=np.int32)
    active = np.ones(c.shape, dtype=bool)
    for i in range(cap):
        z[active] = z[active] * z[active] + c[active]
        escaped = active & (np.abs(z) > ESCAPE_RADIUS)
        counts[escaped] = i
        active &= ~escaped
        if not active.any():
            break
    return counts


# A handful of documented windows: the whole set followed by two deeper zooms
# into the seahorse valley and a minibrot off the western antenna. The deeper
# zooms carry a higher iteration cap, since the escape times near the boundary
# grow as the window shrinks.
ZOOMS: dict[str, Region] = {
    "full": Region(
        min_real=-2.0,
        max_real=0.5,
        min_imag=-1.2,
        max_imag=1.2,
        width=900,
        max_iter=200,
        name="full",
    ),
    "seahorse": Region(
        min_real=-1.28,
        max_real=-1.094,
        min_imag=0.21,
        max_imag=0.42,
        width=900,
        max_iter=400,
        name="seahorse",
    ),
    "minibrot": Region(
        min_real=-1.190,
        max_real=-1.184,
        min_imag=0.300,
        max_imag=0.309,
        width=900,
        max_iter=600,
        name="minibrot",
    ),
}

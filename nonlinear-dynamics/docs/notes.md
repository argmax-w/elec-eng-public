# Method notes

The maths behind each experiment, kept out of the notebooks so the notebooks can
stay about the pictures. What follows is four short derivations, one per
experiment: where the logistic map loses stability, what the Lyapunov exponent
actually measures, how the Mandelbrot render decides what is inside, and why the
Kuramoto coupling has a threshold.

## The logistic map

The logistic map is the one-dimensional recurrence

```
x_{n+1} = r x_n (1 - x_n),    x_n in [0, 1],    r in [0, 4].
```

It is the discrete-time cousin of logistic growth: the linear term `r x` is the
growth and the quadratic term `-r x^2` is the crowding that limits it. For
`r <= 4` the unit interval maps into itself, so iterates stay bounded.

Fixed points solve `x = r x (1 - x)`. There is always the trivial `x* = 0`, and
for `r > 1` a second at `x* = 1 - 1/r`. A fixed point is stable when the
derivative there has magnitude below one. The derivative is `f'(x) = r - 2 r x`,
so at `x* = 1 - 1/r` it equals `2 - r`. That makes the non-trivial fixed point
stable for `1 < r < 3`, and it loses stability at `r = 3`, where the first period
doubling happens. Doublings to period 4, 8, 16 and so on accumulate at
`r ≈ 3.5699`, the onset of chaos. Beyond that the dynamics are chaotic apart from
narrow periodic windows, the widest being the period-3 window near `r = 3.83`.

## The Lyapunov exponent

The Lyapunov exponent is the average exponential rate at which nearby orbits
separate. For a one-dimensional map it is

```
lambda = lim_{N -> inf} (1/N) sum_{n=0}^{N-1} log|f'(x_n)|,
```

the long-run average of the log-derivative along the orbit. For the logistic
map `f'(x) = r - 2 r x`, so

```
lambda = mean of log|r - 2 r x_n| on the attractor.
```

A negative exponent means perturbations shrink on average, the mark of a stable
periodic attractor. A positive exponent means they grow, which is what chaos is.
The exponent passes through zero at each bifurcation. Computed across a grid of
`r` it lines up with the bifurcation diagram, negative in the periodic windows
and positive in the chaotic bands.

A transient is discarded before averaging so the orbit has settled onto the
attractor; otherwise the approach contaminates the mean.

## Escape-time rendering of the Mandelbrot set

The Mandelbrot set is the set of complex parameters `c` for which the iteration

```
z_{n+1} = z_n^2 + c,    z_0 = 0
```

remains bounded. The escape radius is the trick that makes it computable: if
`|z_n|` ever exceeds 2 the orbit is guaranteed to diverge, so 2 is where you can
safely stop. The escape time, the first iteration at which `|z_n| > 2`, is
recorded for each `c` and used to shade the exterior. Points that survive to the
iteration cap are taken to be inside the set.

The render is vectorised over the complex grid. A boolean mask marks the pixels
still bounded, the squaring step runs only on those pixels, newly escaped pixels
have their escape time recorded and drop out of the active set, and the loop
stops early once every pixel has escaped. The iteration cap is raised for the
deeper zooms, where escape times near the boundary grow as the window shrinks.

## The Kuramoto model

The Kuramoto model couples `N` phase oscillators, each with its own natural
frequency `omega_i`, through a sine of their phase differences:

```
dtheta_i/dt = omega_i + (K / N) sum_j sin(theta_j - theta_i).
```

The collective state is summarised by the complex order parameter

```
r e^{i psi} = (1/N) sum_j e^{i theta_j}.
```

The magnitude `r`, the phase coherence, runs from 0, when the phases are spread
uniformly round the circle and cancel, to 1, when they are aligned. `psi` is the
mean phase. Rewriting the coupling in terms of the order parameter gives

```
dtheta_i/dt = omega_i + K r sin(psi - theta_i),
```

so each oscillator is pulled towards the mean phase with a strength proportional
to the coherence itself. That self-reinforcement is what gives the threshold:
below a critical coupling `K_c`, set by the spread of natural frequencies, the
population stays incoherent and `r` hovers near zero; above it a synchronised
cluster forms and `r` rises towards one. For a cicada chorus, the oscillators are
the individual callers, the natural frequencies their slightly different rhythms,
and the coupling their tendency to fall in with what they hear around them.

The simulation integrates the phases with explicit Euler at a small fixed step.
The all-pairs coupling sum is formed by broadcasting the outer phase differences
rather than looping over oscillator pairs.

# elec-eng-public

This repository comprises four of projects, each pulled out of an old exploratory notebook and rebuilt into a package you can install and run:

- a power-systems fault analyser
- a synthetic EV charging-demand generator
- a grid-following inverter model, and
- a set of nonlinear-dynamics experiments.

The notebooks they grew from ran once and then went stale. Here each one is a proper library, with the scripts, tests and figures to back it up.

## Projects

| Project | What it does | Stack |
| --- | --- | --- |
| [`sequence-analysis`](sequence-analysis) | Splits three-phase battery telemetry into symmetrical (zero / positive / negative) sequence components to read fault signatures over time. | numpy, scipy, pandas, matplotlib |
| [`ev-attendance-generator`](ev-attendance-generator) | Builds a synthetic car-park charging-demand profile from an arrival/departure model and sums it into a 24-hour load curve. | numpy, scipy, pandas, matplotlib |
| [`inverter-model`](inverter-model) | A time-domain grid-following inverter: boost stage, sinusoidal PWM, output filter and an analogue PLL that locks to the grid. | numpy, pandas, matplotlib |
| [`nonlinear-dynamics`](nonlinear-dynamics) | Logistic-map bifurcation and Lyapunov exponents, escape-time Mandelbrot rendering, and a Kuramoto model of cicada chorus synchronisation. | numpy, scipy, pandas, matplotlib |

## Layout

Every project has the same shape, so once you have found your way around one you know them all:

```
<project>/
  README.md            overview, results, how to run it
  pyproject.toml       installable package (pip install -e .)
  src/<package>/       the library: I/O, models, plotting helpers
  scripts/             the heavy computation
  notebooks/           analysis notebooks with the figures
  docs/                method notes
  tests/               unit tests
```

The heavy computation runs in `scripts/`, which write their results to
`artifacts/`; the notebooks just read those and make the figures. The split
keeps the slow work in one place and leaves each notebook light enough to open
and follow.

## Withheld cores

Two of these projects keep a small piece of original work out of the public
release. In `sequence-analysis` it is the sequence-decomposition kernel; in
`ev-attendance-generator` it is the generation engine and the fitted
parameters. Those files are encrypted in place with
[git-crypt](https://github.com/AGWA/git-crypt), so the repository carries the
full encrypted blob but not the key. Everything around them is open, and each
affected project explains the arrangement in its own README.

## Getting started

```bash
mamba env create -f environment.yml
conda activate elec-eng-public

cd inverter-model      # or any other project
pip install -e .
python scripts/run_simulation.py
jupyter lab            # open and run the notebooks
```

## Licence

MIT for the code. See `LICENSE`.

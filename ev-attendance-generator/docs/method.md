# Method

The whole model is two curves per group and some honest bookkeeping on top. This
note sets out the behavioural densities, how they turn into a load curve, and
which pieces are held back.

## The behavioural model

Each behavioural group is described by two densities over the hour of the day: an
arrival density and a departure density, each a weighted mixture of Gaussians,

$$
f(t) \propto \sum_k w_k \, \mathcal{N}(t \mid \mu_k, \sigma_k),
$$

normalised to unit area over the 24-hour grid. The shape of the mixture is the
behaviour. A bimodal arrival density gives a morning rush plus an afternoon
shoulder. A narrow single Gaussian gives a group that arrives at much the same
time.

## From densities to a load curve

1. **Sample dwell times.** For each vehicle, draw an arrival time from the
   arrival density and a departure time from the departure density. The departure
   has to fall after the arrival, which I enforce by rejection sampling: redraw it
   until it does. Each vehicle is then a real arrival-to-departure interval, not
   two independent draws.
2. **Count occupancy.** At each time step, count the vehicles whose interval spans
   it. That is the occupancy curve for the group.
3. **Scale to power.** Multiply occupancy by the charger rating for the group's
   charging load, then sum the groups for the car-park total.

The peak of the total is what the supply must be sized for. The groups overlap
only partially and each spreads over time, so the peak sits well below the sum of
every charger's rating. That gap is the diversity benefit, and it is the reason a
behavioural model is worth the trouble.

## What is withheld

The mixture construction, the constrained sampling, and the occupancy count live
in `src/evattendance/_engine.py`. The fitted parameters (the mixtures, fleet
sizes, and charger rating) live in `src/evattendance/_params.py`. Both are
encrypted with git-crypt and not published in readable form. This document
describes the standard approach. The specific implementation and the fitted
numbers are withheld.

# Method

This note is the theory the decomposition rests on: how three unbalanced
phasors become three balanced sequences, how each phasor is pulled out one cycle
at a time, and what the harmonic cross-check leans on. The numerical kernel that
implements it is withheld; the maths behind it is not.

## Symmetrical components

Fortescue's theorem is the lever the whole project turns on. It splits any set
of three phasors into three balanced sets: a positive-sequence set rotating the
normal way, a negative-sequence set rotating against it, and a zero-sequence set
with no rotation at all. With the rotation operator $a = e^{j2\pi/3}$ the phase
phasors $[V_a, V_b, V_c]$ map to the sequence phasors $[V_0, V_1, V_2]$ through

$$
\begin{bmatrix} V_0 \\ V_1 \\ V_2 \end{bmatrix}
= \frac{1}{3}
\begin{bmatrix} 1 & 1 & 1 \\ 1 & a & a^2 \\ 1 & a^2 & a \end{bmatrix}
\begin{bmatrix} V_a \\ V_b \\ V_c \end{bmatrix}.
$$

A balanced supply has only $V_1$. Negative sequence $V_2$ comes from the rotating
asymmetry of an unbalanced fault, the phase-to-phase fault being the textbook
case. Zero sequence $V_0$ comes from the common-mode asymmetry of an earth fault.
The ratio $|V_2|/|V_1|$ is the standard voltage-unbalance factor.

## Fundamental phasor per cycle

The transform needs one phasor per phase, so each phase is first reduced to its
fundamental amplitude and phase over one cycle by correlating it against a unit
phasor template at the fundamental. That is a single-bin matched filter,
equivalent to the fundamental Fourier coefficient. Slide the one-cycle window one
sample at a time and the sequence components fall out as functions of time.

## Harmonic sequence classification

The harmonic reading in notebook 01 leans on a tidy result from the
balanced-system case: harmonic order $3m+1$ is positive sequence, $3m+2$ negative
and $3m$ zero. Group the windowed spectrum into integer harmonics, average the
magnitudes by class, and you have an approximate cross-check on the direct phasor
method. Treat it as a sanity check, not the answer.

## What is withheld

The per-cycle phasor estimate, the inverse symmetrical-component transform and the
harmonic classification are all implemented in `src/seqanalysis/_kernel.py`, which
is encrypted with git-crypt and not published in readable form. This document
covers the standard theory behind them. The specific implementation is withheld.

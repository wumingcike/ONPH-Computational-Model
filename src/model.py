"""ONPH discrete-time stochastic difference-equation model.

This module replaces the three hard-coded scenarios of ``117-111.py`` with
orthogonal factor switches.  The mechanisms named by the hypothesis
(wake confirmation, homeostatic downscaling, gated replay, endogenous
instinct drive) become independent arguments, so every one of them can be
turned off while the others stay on.

Equation (one day = one wake/sleep cycle):

    u_t      = 0.9                         if t == 1   (encoding)
             = c * exp(-0.2 * (t - 1))     if t >= 2   (confirmation strength c)
    w_wake   = B( w_{t-1} + gamma * u_t )
    g        = sigmoid(kappa * (w_wake - theta))      [gating = "sigmoid"]
             = w_wake                                 [gating = "linear"]
             = 1                                      [gating = "none"]
    r_t      = g * N(0.9, 0.2)                        (replay)
    s_t      = N(1.0, 0.05)                           (downscaling)
    w_t      = B( w_wake + alpha * r_t - beta * s_t + delta * instinct + N(0, noise) )

``B`` is the boundary operator: hard clip (default), reflecting fold, or the
identity for the unbounded robustness control.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

import numpy as np

BOUNDS = ("clip", "fold", "none")
GATINGS = ("sigmoid", "linear", "none")


@dataclass(frozen=True)
class Params:
    """Parameter set.  Defaults are the original calibrated values."""

    alpha: float = 0.22          # replay potentiation gain
    beta: float = 0.18           # homeostatic downscaling pressure
    gamma: float = 0.70          # wake-confirmation gain
    delta: float = 0.18          # endogenous instinct drive
    noise: float = 0.08          # additive biological noise
    theta: float = 0.65          # replay gate threshold
    kappa: float = 12.0          # replay gate steepness
    replay_mean: float = 0.9
    replay_sd: float = 0.2
    down_mean: float = 1.0
    down_sd: float = 0.05
    wake_sd: float = 0.10
    decay: float = 0.2           # decay rate of the confirmation signal
    bounds: str = "clip"

    def with_(self, **kw) -> "Params":
        return replace(self, **kw)


def _bound(w: np.ndarray, mode: str) -> np.ndarray:
    if mode == "clip":
        return np.clip(w, 0.0, 1.0)
    if mode == "fold":
        w = np.abs(w)
        w = np.where(w > 1.0, 2.0 - w, w)
        return np.clip(np.abs(w), 0.0, 1.0)
    if mode == "none":
        return w
    raise ValueError(f"unknown bounds mode: {mode}")


def _truncnorm_pos(mean: float, sd: float, n: int, rng) -> np.ndarray:
    """Normal(mean, sd) truncated at zero, by rejection (unbiased, m4)."""
    if mean <= 1e-9:
        return np.zeros(n)
    z = rng.standard_normal(n)
    bad = z < -mean / sd
    while bad.any():
        z[bad] = rng.standard_normal(int(bad.sum()))
        bad = z < -mean / sd
    return mean + sd * z


def confirmation_input(day: int, strength: float, decay: float = 0.2,
                       first_day: float = 0.9) -> float:
    """Mean external drive on a given day.

    ``strength = 0`` means a single unreinforced exposure (the memory is
    encoded on day 1 and never confirmed again).
    """
    if day == 1:
        return first_day
    return strength * np.exp(-decay * (day - 1))


def simulate(p: Params, *, n: int, days: int = 7, confirm: float = 0.6,
             gating: str = "sigmoid", instinct: bool = False,
             w0: float = 0.05, seed: int = 0,
             first_day: float = 0.9) -> np.ndarray:
    """Run ``n`` independent Monte Carlo trajectories.

    Returns an array of shape ``(n, days + 1)``; column 0 is the initial
    weight.  All arms share the same initial weight by default (M3).
    """
    if gating not in GATINGS:
        raise ValueError(f"unknown gating: {gating}")
    rng = np.random.default_rng(seed)
    w = np.full(n, float(w0))
    out = np.empty((n, days + 1))
    out[:, 0] = w
    inst = p.delta if instinct else 0.0

    for d in range(1, days + 1):
        u_mean = confirmation_input(d, confirm, p.decay, first_day)
        u = _truncnorm_pos(u_mean, p.wake_sd, n, rng)

        w_wake = _bound(w + p.gamma * u, p.bounds)

        if gating == "sigmoid":
            g = 1.0 / (1.0 + np.exp(-p.kappa * (w_wake - p.theta)))
        elif gating == "linear":
            g = w_wake
        else:
            g = np.ones(n)

        replay = g * rng.normal(p.replay_mean, p.replay_sd, n)
        down = rng.normal(p.down_mean, p.down_sd, n)

        dw = (p.alpha * replay - p.beta * down + inst
              + rng.normal(0.0, p.noise, n))
        w = _bound(w_wake + dw, p.bounds)
        out[:, d] = w

    return out


def gate_value(p: Params, w: float, gating: str = "sigmoid") -> float:
    if gating == "sigmoid":
        return float(1.0 / (1.0 + np.exp(-p.kappa * (w - p.theta))))
    if gating == "linear":
        return float(w)
    return 1.0

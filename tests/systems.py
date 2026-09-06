"""Deterministic test systems with known embedding answers.

Integrated with fixed-step fourth-order Runge-Kutta written in plain arithmetic.
Both right-hand sides are polynomial, so with IEEE-754 doubles the trajectories are
bit-identical on every platform. An adaptive solver (scipy's DOP853) was not: chaos
amplified the last-bit differences between macOS and Linux libm into different
trajectories, and on Lorenz the autocorrelation zero crossing, hence the chosen
delay and the dimension verdict, changed with the trajectory (found 2026-09-06 when
CI failed on Linux with the same code that passed locally).
"""

import numpy as np

TRANSIENT = 2000


def _rk4(rhs, x0, n, dt):
    state = np.array(x0, dtype=float)
    out = np.empty(n + TRANSIENT)
    for i in range(n + TRANSIENT):
        out[i] = state[0]
        k1 = rhs(state)
        k2 = rhs(state + 0.5 * dt * k1)
        k3 = rhs(state + 0.5 * dt * k2)
        k4 = rhs(state + dt * k3)
        state = state + (dt / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4)
    return out[TRANSIENT:]


def lorenz(n, dt=0.01, seed=0):
    """x component of the Lorenz system (sigma=10, rho=28, beta=8/3). Attractor dimension 2.06."""
    rng = np.random.default_rng(seed)
    x0 = rng.normal(size=3) + np.array([1.0, 1.0, 20.0])

    def rhs(s):
        x, y, z = s
        return np.array([10.0 * (y - x), x * (28.0 - z) - y, x * y - 8.0 / 3.0 * z])

    return _rk4(rhs, x0, n, dt)


def rossler(n, dt=0.05, seed=0):
    """x component of the Rossler system (a=b=0.2, c=5.7). Attractor dimension 2.01."""
    rng = np.random.default_rng(seed)
    x0 = rng.normal(size=3) + np.array([1.0, 1.0, 0.0])

    def rhs(s):
        x, y, z = s
        return np.array([-y - z, x + 0.2 * y, 0.2 + z * (x - 5.7)])

    return _rk4(rhs, x0, n, dt)

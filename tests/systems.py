"""Deterministic test systems with known embedding answers."""

import numpy as np
from scipy.integrate import solve_ivp

TRANSIENT = 2000


def _integrate(rhs, x0, n, dt):
    t_eval = np.arange(n + TRANSIENT) * dt
    sol = solve_ivp(
        rhs, (0.0, t_eval[-1]), x0, t_eval=t_eval, rtol=1e-9, atol=1e-12, method="DOP853"
    )
    return sol.y[0, TRANSIENT:]


def lorenz(n, dt=0.01, seed=0):
    """x component of the Lorenz system (sigma=10, rho=28, beta=8/3). Attractor dimension 2.06."""
    rng = np.random.default_rng(seed)
    x0 = rng.normal(size=3) + np.array([1.0, 1.0, 20.0])

    def rhs(t, s):
        x, y, z = s
        return [10.0 * (y - x), x * (28.0 - z) - y, x * y - 8.0 / 3.0 * z]

    return _integrate(rhs, x0, n, dt)


def rossler(n, dt=0.05, seed=0):
    """x component of the Rossler system (a=b=0.2, c=5.7). Attractor dimension 2.01."""
    rng = np.random.default_rng(seed)
    x0 = rng.normal(size=3) + np.array([1.0, 1.0, 0.0])

    def rhs(t, s):
        x, y, z = s
        return [-y - z, x + 0.2 * y, 0.2 + z * (x - 5.7)]

    return _integrate(rhs, x0, n, dt)

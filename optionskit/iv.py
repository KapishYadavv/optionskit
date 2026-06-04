"""Implied volatility solver for European options under Black-Scholes."""

from __future__ import annotations

import math

from scipy.optimize import brentq

from .pricing import black_scholes


def implied_vol(
    price: float,
    S: float,
    K: float,
    T: float,
    r: float,
    kind: str = "call",
    *,
    low: float = 1e-6,
    high: float = 5.0,
    tol: float = 1e-8,
) -> float:
    """Solve for the volatility that makes Black-Scholes match ``price``.

    Uses Brent's method on ``BS(sigma) - price``. Returns sigma as a decimal
    (e.g. ``0.20`` means 20% vol).

    Parameters
    ----------
    price : float
        Observed option price.
    S, K, T, r : float
        Spot, strike, time-to-expiry (years), risk-free rate.
    kind : {"call", "put"}
    low, high : float
        Volatility search bracket. Defaults span 0.0001% to 500%.
    tol : float
        Convergence tolerance on sigma.

    Raises
    ------
    ValueError
        If ``T <= 0`` or the price is outside no-arbitrage bounds (below
        intrinsic / above the option's upper bound), so no IV exists.
    """
    if kind not in ("call", "put"):
        raise ValueError(f"kind must be 'call' or 'put', got {kind!r}")
    if T <= 0:
        raise ValueError("implied_vol requires T > 0")
    if price < 0:
        raise ValueError("price cannot be negative")

    disc_K = K * math.exp(-r * T)
    if kind == "call":
        intrinsic = max(S - disc_K, 0.0)
        upper = S
    else:
        intrinsic = max(disc_K - S, 0.0)
        upper = disc_K

    if price < intrinsic - 1e-10:
        raise ValueError(
            f"price {price} is below intrinsic value {intrinsic:.6f}; no IV exists"
        )
    if price > upper + 1e-10:
        raise ValueError(
            f"price {price} exceeds no-arbitrage upper bound {upper:.6f}; no IV exists"
        )

    def f(sigma: float) -> float:
        return float(black_scholes(S, K, T, r, sigma, kind)) - price

    f_lo, f_hi = f(low), f(high)
    if f_lo * f_hi > 0:
        # Widen the bracket once before giving up; useful for deep-ITM puts etc.
        f_hi2 = f(high * 2)
        if f_lo * f_hi2 > 0:
            raise ValueError(
                "Could not bracket a root in [low, 2*high]; check inputs."
            )
        high = high * 2

    return float(brentq(f, low, high, xtol=tol))

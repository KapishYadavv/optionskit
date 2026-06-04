"""Closed-form Black-Scholes Greeks for European options.

All Greeks are returned as raw mathematical derivatives:

* ``theta`` is per year. Pass ``per_day=True`` for the trader-friendly daily decay.
* ``vega`` is per 1.0 change in sigma (i.e. per 100 vol-points). Divide by 100
  to get "vega per 1% vol" — pass ``per_percent=True``.
* ``rho`` is per 1.0 change in r. Divide by 100 for "rho per 1% rate" —
  pass ``per_percent=True``.
"""

from __future__ import annotations

import numpy as np
from scipy.stats import norm


def _d1_d2(S, K, T, r, sigma):
    S = np.asarray(S, dtype=float)
    K = np.asarray(K, dtype=float)
    T = np.asarray(T, dtype=float)
    sigma = np.asarray(sigma, dtype=float)
    sqrtT = np.sqrt(T)
    d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * sqrtT)
    d2 = d1 - sigma * sqrtT
    return d1, d2


def _scalar(arr):
    return arr if arr.ndim else float(arr)


def delta(S, K, T, r, sigma, kind: str = "call"):
    """Black-Scholes delta. ``∂Price/∂S``."""
    if kind not in ("call", "put"):
        raise ValueError(f"kind must be 'call' or 'put', got {kind!r}")
    d1, _ = _d1_d2(S, K, T, r, sigma)
    return _scalar(norm.cdf(d1) if kind == "call" else norm.cdf(d1) - 1.0)


def gamma(S, K, T, r, sigma):
    """Black-Scholes gamma (same for call and put). ``∂²Price/∂S²``."""
    S = np.asarray(S, dtype=float)
    sigma = np.asarray(sigma, dtype=float)
    T = np.asarray(T, dtype=float)
    d1, _ = _d1_d2(S, K, T, r, sigma)
    return _scalar(norm.pdf(d1) / (S * sigma * np.sqrt(T)))


def vega(S, K, T, r, sigma, per_percent: bool = False):
    """Black-Scholes vega (same for call and put). ``∂Price/∂σ``.

    Set ``per_percent=True`` to scale to "per 1% vol" (i.e. divide by 100).
    """
    S = np.asarray(S, dtype=float)
    T = np.asarray(T, dtype=float)
    d1, _ = _d1_d2(S, K, T, r, sigma)
    v = S * norm.pdf(d1) * np.sqrt(T)
    if per_percent:
        v = v / 100.0
    return _scalar(v)


def theta(S, K, T, r, sigma, kind: str = "call", per_day: bool = False):
    """Black-Scholes theta. ``∂Price/∂T_remaining`` with a sign flip (decay).

    Returned in per-year units by default. ``per_day=True`` divides by 365.
    """
    if kind not in ("call", "put"):
        raise ValueError(f"kind must be 'call' or 'put', got {kind!r}")
    S = np.asarray(S, dtype=float)
    K = np.asarray(K, dtype=float)
    T = np.asarray(T, dtype=float)
    sigma = np.asarray(sigma, dtype=float)
    d1, d2 = _d1_d2(S, K, T, r, sigma)
    term1 = -(S * norm.pdf(d1) * sigma) / (2.0 * np.sqrt(T))
    if kind == "call":
        t = term1 - r * K * np.exp(-r * T) * norm.cdf(d2)
    else:
        t = term1 + r * K * np.exp(-r * T) * norm.cdf(-d2)
    if per_day:
        t = t / 365.0
    return _scalar(t)


def rho(S, K, T, r, sigma, kind: str = "call", per_percent: bool = False):
    """Black-Scholes rho. ``∂Price/∂r``.

    Set ``per_percent=True`` to scale to "per 1% rate" (i.e. divide by 100).
    """
    if kind not in ("call", "put"):
        raise ValueError(f"kind must be 'call' or 'put', got {kind!r}")
    K = np.asarray(K, dtype=float)
    T = np.asarray(T, dtype=float)
    _, d2 = _d1_d2(S, K, T, r, sigma)
    if kind == "call":
        rh = K * T * np.exp(-r * T) * norm.cdf(d2)
    else:
        rh = -K * T * np.exp(-r * T) * norm.cdf(-d2)
    if per_percent:
        rh = rh / 100.0
    return _scalar(rh)


def greeks(S, K, T, r, sigma, kind: str = "call") -> dict:
    """Return all five Greeks in a single dict (raw units)."""
    return {
        "delta": delta(S, K, T, r, sigma, kind),
        "gamma": gamma(S, K, T, r, sigma),
        "vega": vega(S, K, T, r, sigma),
        "theta": theta(S, K, T, r, sigma, kind),
        "rho": rho(S, K, T, r, sigma, kind),
    }

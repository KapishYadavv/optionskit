"""Closed-form Black-Scholes Greeks."""

from __future__ import annotations

import numpy as np
from scipy.stats import norm


def _d1(S, K, T, r, sigma):
    S = np.asarray(S, dtype=float)
    K = np.asarray(K, dtype=float)
    T = np.asarray(T, dtype=float)
    sigma = np.asarray(sigma, dtype=float)
    return (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))


def delta(S, K, T, r, sigma, kind: str = "call"):
    """Black-Scholes delta."""
    if kind not in ("call", "put"):
        raise ValueError(f"kind must be 'call' or 'put', got {kind!r}")
    d1 = _d1(S, K, T, r, sigma)
    out = norm.cdf(d1) if kind == "call" else norm.cdf(d1) - 1.0
    return out if out.ndim else float(out)


def gamma(S, K, T, r, sigma):
    """Black-Scholes gamma (identical for call and put)."""
    S = np.asarray(S, dtype=float)
    sigma = np.asarray(sigma, dtype=float)
    T = np.asarray(T, dtype=float)
    d1 = _d1(S, K, T, r, sigma)
    out = norm.pdf(d1) / (S * sigma * np.sqrt(T))
    return out if out.ndim else float(out)

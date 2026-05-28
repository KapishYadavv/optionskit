# Black-Scholes pricing 
# FOR European options ONLY.

from __future__ import annotations

import numpy as np
from scipy.stats import norm


def black_scholes(S, K, T, r, sigma, kind: str = "call"):
    """Price a European option under Black-Scholes.

    Parameters
    ----------
    S : float or array
        Spot price of the underlying.
    K : float or array
        Strike price.
    T : float or array
        Time to expiry in years.
    r : float
        Risk-free rate (continuously compounded).
    sigma : float or array
        Volatility (annualized).
    kind : {"call", "put"}
        Option type.
    """
    if kind not in ("call", "put"):
        raise ValueError(f"kind must be 'call' or 'put', got {kind!r}")

    S = np.asarray(S, dtype=float)
    K = np.asarray(K, dtype=float)
    T = np.asarray(T, dtype=float)
    sigma = np.asarray(sigma, dtype=float)

    intrinsic = np.maximum(S - K, 0.0) if kind == "call" else np.maximum(K - S, 0.0)

    expired = T <= 0
    if np.all(expired):
        return intrinsic if intrinsic.ndim else float(intrinsic)

    with np.errstate(divide="ignore", invalid="ignore"):
        sqrtT = np.sqrt(np.where(expired, 1.0, T))
        d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * sqrtT)
        d2 = d1 - sigma * sqrtT

        if kind == "call":
            price = S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
        else:
            price = K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)

    price = np.where(expired, intrinsic, price)
    return price if price.ndim else float(price)

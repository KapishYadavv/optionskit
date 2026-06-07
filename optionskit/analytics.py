"""Derived analytics for a Strategy: portfolio Greeks, summary stats,
probability of profit, and the time-decay overlay plot.

Everything here assumes a *single* expiry ``T`` and a *single* volatility
``sigma`` shared across all option legs — consistent with the rest of the
library (the payoff is a single-expiry construct). Stock legs contribute a
delta of ``qty`` per unit and zero to the other Greeks.
"""

from __future__ import annotations

import math

import numpy as np
from scipy.stats import norm

from .greeks import delta as _delta, gamma as _gamma, vega as _vega, theta as _theta, rho as _rho
from .pricing import black_scholes

INF = float("inf")


# ----------------------------------------------------------------------
# Portfolio Greeks
# ----------------------------------------------------------------------
def portfolio_greeks(strategy, spot: float, T: float, r: float = 0.0, sigma: float = 0.20) -> dict:
    """Net delta/gamma/vega/theta/rho of the whole position.

    Greeks are summed across legs in the library's per-unit convention
    (the same units as ``payoff``). ``theta`` is per-year; divide by 365 for
    per-day. Stock legs add ``qty`` to delta and nothing else.
    """
    if not strategy.legs:
        raise ValueError("Strategy has no legs.")
    if T <= 0:
        raise ValueError("portfolio_greeks requires T > 0.")

    totals = {"delta": 0.0, "gamma": 0.0, "vega": 0.0, "theta": 0.0, "rho": 0.0}
    for leg in strategy.legs:
        if leg.kind == "stock":
            totals["delta"] += leg.qty
            continue
        totals["delta"] += leg.qty * _delta(spot, leg.strike, T, r, sigma, leg.kind)
        totals["gamma"] += leg.qty * _gamma(spot, leg.strike, T, r, sigma)
        totals["vega"] += leg.qty * _vega(spot, leg.strike, T, r, sigma)
        totals["theta"] += leg.qty * _theta(spot, leg.strike, T, r, sigma, leg.kind)
        totals["rho"] += leg.qty * _rho(spot, leg.strike, T, r, sigma, leg.kind)
    return {k: float(v) for k, v in totals.items()}


# ----------------------------------------------------------------------
# Summary statistics
# ----------------------------------------------------------------------
def summary(strategy) -> dict:
    """Key payoff statistics at expiry.

    Returns ``max_profit``, ``max_loss`` (``inf`` / ``-inf`` when unbounded),
    ``breakevens`` (sorted list), ``net_premium`` (signed: ``+`` = net debit
    paid, ``-`` = net credit received), and ``risk_reward`` (risk per unit
    reward, or ``None`` if either side is unbounded).
    """
    if not strategy.legs:
        raise ValueError("Strategy has no legs.")

    strikes = sorted({leg.strike for leg in strategy.legs})
    premiums = [leg.premium for leg in strategy.legs if leg.kind != "stock"]

    # --- extrema: payoff is piecewise-linear, so the optima sit at vertices
    # (S=0 and each strike) or at +inf. The underlying can't go below 0, so the
    # downside is always bounded; only the S -> +inf side can be unbounded.
    candidates = np.array([0.0] + strikes, dtype=float)
    cand_pnl = strategy.payoff(candidates)
    right_slope = sum(leg.qty for leg in strategy.legs if leg.kind in ("call", "stock"))

    max_profit = INF if right_slope > 1e-9 else float(cand_pnl.max())
    max_loss = -INF if right_slope < -1e-9 else float(cand_pnl.min())

    # --- breakevens on a fine grid with strikes pinned as exact knots
    pad = 3.0 * (max(premiums) if premiums else max(strikes) * 0.5)
    hi = max(strikes) * 1.5 + pad
    grid = np.unique(np.concatenate([np.linspace(0.0, hi, 4000), candidates]))
    bes = strategy.breakevens(grid, strategy.payoff(grid))

    net_premium = float(sum(leg.qty * leg.premium for leg in strategy.legs if leg.kind != "stock"))

    risk_reward = None
    if math.isfinite(max_profit) and math.isfinite(max_loss) and max_profit > 0:
        risk_reward = abs(max_loss) / max_profit

    return {
        "max_profit": max_profit,
        "max_loss": max_loss,
        "breakevens": [round(b, 6) for b in bes],
        "net_premium": net_premium,
        "risk_reward": risk_reward,
    }


# ----------------------------------------------------------------------
# Probability of profit
# ----------------------------------------------------------------------
def probability_of_profit(
    strategy, spot: float, T: float, r: float = 0.0, sigma: float = 0.20, drift: float | None = None
) -> float:
    """Probability the strategy finishes profitable at expiry.

    Models the terminal price as lognormal with drift ``drift`` (defaults to
    the risk-neutral ``r``) and volatility ``sigma``. Integrates that density
    over the regions where the expiry payoff is >= 0. Returns a value in [0, 1].
    """
    if not strategy.legs:
        raise ValueError("Strategy has no legs.")
    if T <= 0:
        raise ValueError("probability_of_profit requires T > 0.")
    if sigma <= 0:
        raise ValueError("probability_of_profit requires sigma > 0.")

    mu = r if drift is None else drift
    s = summary(strategy)
    edges = [0.0] + list(s["breakevens"]) + [INF]

    denom = sigma * math.sqrt(T)
    drift_term = (mu - 0.5 * sigma**2) * T

    def cdf(x: float) -> float:
        # P(S_T <= x)
        if x <= 0:
            return 0.0
        if x == INF:
            return 1.0
        return float(norm.cdf((math.log(x / spot) - drift_term) / denom))

    pop = 0.0
    for a, b in zip(edges[:-1], edges[1:]):
        # representative interior point to test the sign of the payoff on (a, b)
        if b == INF:
            mid = (a if a > 0 else spot) * 1.5 + 1.0
        else:
            mid = 0.5 * (a + b)
        if float(strategy.payoff(np.array([mid]))[0]) >= 0:
            pop += cdf(b) - cdf(a)
    return float(min(max(pop, 0.0), 1.0))


# ----------------------------------------------------------------------
# Time-decay overlay
# ----------------------------------------------------------------------
def _mtm(strategy, spots: np.ndarray, T: float, r: float, sigma: float) -> np.ndarray:
    """Mark-to-market value of the strategy across spots at remaining time T."""
    spots = np.asarray(spots, dtype=float)
    total = np.zeros_like(spots)
    for leg in strategy.legs:
        if leg.kind == "stock":
            total += leg.qty * (spots - leg.strike)
        else:
            price = black_scholes(spots, leg.strike, T, r, sigma, leg.kind)
            total += leg.qty * (np.asarray(price, dtype=float) - leg.premium)
    return total


def _blend(c1, c2, t):
    """Linear blend between two RGB hex colors; returns an 'rgb(...)' string."""
    a = tuple(int(c1[i : i + 2], 16) for i in (1, 3, 5))
    b = tuple(int(c2[i : i + 2], 16) for i in (1, 3, 5))
    rgb = tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))
    return f"rgb({rgb[0]},{rgb[1]},{rgb[2]})"


def plot_time_decay(
    strategy,
    T: float,
    days_to_expiry=None,
    spot_range=None,
    r: float = 0.0,
    sigma: float = 0.20,
    title: str = "Time decay — value as expiry approaches",
):
    """Overlay the strategy's value at several days-to-expiry snapshots.

    ``T`` is the current time to expiry in years (the longest-dated curve).
    ``days_to_expiry`` is a list of remaining-day snapshots to draw; the
    default fans out from the full term down to 0 (the expiry payoff).
    """
    import plotly.graph_objects as go

    if not strategy.legs:
        raise ValueError("Strategy has no legs.")
    if T <= 0:
        raise ValueError("plot_time_decay requires T > 0.")

    strikes = [leg.strike for leg in strategy.legs]
    if spot_range is None:
        lo, hi = 0.7 * min(strikes), 1.3 * max(strikes)
    else:
        lo, hi = spot_range
    spots = np.linspace(lo, hi, 400)

    total_days = T * 365.0
    if days_to_expiry is None:
        raw = [total_days, total_days * 2 / 3, total_days / 3, 0]
        days_to_expiry = sorted({round(d) for d in raw}, reverse=True)
    else:
        days_to_expiry = sorted({float(d) for d in days_to_expiry}, reverse=True)

    fig = go.Figure()
    n = len(days_to_expiry)
    for idx, d in enumerate(days_to_expiry):
        t = max(d / 365.0, 0.0)
        y = _mtm(strategy, spots, t, r, sigma)
        is_expiry = d <= 0
        frac = 0.0 if n == 1 else idx / (n - 1)  # 0 = nearest term, 1 = expiry
        if is_expiry:
            color, width, dash = "#f59e0b", 3.0, "solid"  # amber, bold
            name = "Expiry"
        else:
            color = _blend("#93c5fd", "#1d4ed8", frac)  # light blue -> deep blue
            width, dash = 1.8, "solid"
            name = f"{d:g}d left"
        fig.add_trace(go.Scatter(
            x=spots, y=y, mode="lines", name=name,
            line=dict(color=color, width=width, dash=dash),
            hovertemplate=f"{name}<br>Spot %{{x:.2f}}<br>Value %{{y:+.2f}}<extra></extra>",
        ))

    fig.add_hline(y=0, line=dict(color="rgba(156,163,175,0.6)", width=1))
    for k in sorted(set(strikes)):
        fig.add_vline(x=k, line=dict(color="gray", width=0.7, dash="dash"), opacity=0.4)

    fig.update_layout(
        title=dict(
            text=f"<b>{title}</b>",
            font=dict(size=22, family="Inter, system-ui, sans-serif", color="#e5e7eb"),
            x=0.02, xanchor="left", y=0.95,
        ),
        xaxis=dict(
            title=dict(text="Underlying price", font=dict(size=14, color="#9ca3af")),
            tickfont=dict(size=12, color="#9ca3af"),
            gridcolor="rgba(75, 85, 99, 0.25)", zeroline=False,
        ),
        yaxis=dict(
            title=dict(text="Position value (P&L)", font=dict(size=14, color="#9ca3af")),
            tickfont=dict(size=12, color="#9ca3af"),
            gridcolor="rgba(75, 85, 99, 0.25)", zeroline=False,
        ),
        plot_bgcolor="#0b1020", paper_bgcolor="#0b1020",
        font=dict(family="Inter, system-ui, sans-serif", color="#e5e7eb"),
        margin=dict(l=70, r=40, t=80, b=60),
        hovermode="x unified",
        hoverlabel=dict(bgcolor="#111827", bordercolor="#3b82f6",
                        font=dict(size=12, color="#e5e7eb")),
        legend=dict(font=dict(size=12, color="#e5e7eb"), bgcolor="rgba(17,24,39,0.6)"),
    )
    return fig

"""Scenario stress testing for European option strategies.

A *scenario* is a snapshot of "what if the market did X right now":

* ``spot_shift``  — fractional move in the underlying (``-0.10`` = -10% crash)
* ``vol_shift``   — absolute change in volatility (``+0.05`` = +5 vol points)
* ``days_passed`` — calendar days elapsed (theta decay)

The strategy is re-priced under those shocks using Black-Scholes for the option
legs and a linear mark for any stock legs. The result is the strategy's mark-
to-market P&L *under that scenario* — not at expiry.
"""

from __future__ import annotations

from typing import Iterable

import numpy as np

from .pricing import black_scholes


def _leg_value_now(leg, spot: float, T: float, r: float, sigma: float) -> float:
    """Current mark-to-market P&L of a single leg under the given market state."""
    if leg.kind == "stock":
        return float(leg.qty * (spot - leg.strike))
    # option: cost basis is leg.premium per contract
    price = float(black_scholes(spot, leg.strike, T, r, sigma, kind=leg.kind))
    return float(leg.qty * (price - leg.premium))


def stress_pnl(
    strategy,
    spot: float,
    T: float,
    r: float,
    sigma: float,
    scenario: dict,
) -> float:
    """P&L of ``strategy`` under a single scenario dict."""
    spot_shift = float(scenario.get("spot_shift", 0.0))
    vol_shift = float(scenario.get("vol_shift", 0.0))
    days_passed = float(scenario.get("days_passed", 0.0))

    shocked_spot = spot * (1.0 + spot_shift)
    shocked_sigma = max(sigma + vol_shift, 1e-6)
    shocked_T = max(T - days_passed / 365.0, 1e-9)

    return sum(
        _leg_value_now(leg, shocked_spot, shocked_T, r, shocked_sigma)
        for leg in strategy.legs
    )


def stress_test(
    strategy,
    spot: float,
    T: float,
    scenarios: Iterable[dict],
    r: float = 0.0,
    sigma: float = 0.20,
) -> list[dict]:
    """Evaluate ``strategy`` under each scenario; return enriched dicts."""
    if not strategy.legs:
        raise ValueError("Strategy has no legs.")
    if T <= 0:
        raise ValueError("Base T must be > 0 (option(s) already expired).")
    out = []
    baseline = sum(_leg_value_now(leg, spot, T, r, sigma) for leg in strategy.legs)
    for sc in scenarios:
        pnl = stress_pnl(strategy, spot, T, r, sigma, sc)
        out.append({
            "spot_shift": float(sc.get("spot_shift", 0.0)),
            "vol_shift": float(sc.get("vol_shift", 0.0)),
            "days_passed": float(sc.get("days_passed", 0.0)),
            "pnl": float(pnl),
            "pnl_vs_baseline": float(pnl - baseline),
        })
    return out


def stress_grid(
    strategy,
    spot: float,
    T: float,
    spot_shifts: np.ndarray,
    vol_shifts: np.ndarray,
    days_passed: float = 0.0,
    r: float = 0.0,
    sigma: float = 0.20,
) -> np.ndarray:
    """Compute P&L on the cartesian product of ``spot_shifts`` × ``vol_shifts``.

    Returns a 2D array ``Z`` of shape ``(len(vol_shifts), len(spot_shifts))`` —
    rows are vol axis, columns are spot axis (Plotly heatmap convention).
    """
    spot_shifts = np.asarray(spot_shifts, dtype=float)
    vol_shifts = np.asarray(vol_shifts, dtype=float)
    Z = np.empty((len(vol_shifts), len(spot_shifts)), dtype=float)
    shocked_T = max(T - days_passed / 365.0, 1e-9)
    for i, dv in enumerate(vol_shifts):
        shocked_sigma = max(sigma + float(dv), 1e-6)
        for j, ds in enumerate(spot_shifts):
            shocked_spot = spot * (1.0 + float(ds))
            Z[i, j] = sum(
                _leg_value_now(leg, shocked_spot, shocked_T, r, shocked_sigma)
                for leg in strategy.legs
            )
    return Z


def plot_stress_heatmap(
    strategy,
    spot: float,
    T: float,
    spot_shifts: np.ndarray | None = None,
    vol_shifts: np.ndarray | None = None,
    days_passed: float = 0.0,
    r: float = 0.0,
    sigma: float = 0.20,
    title: str = "Stress test — P&L under spot × vol shocks",
):
    """Render a diverging heatmap of P&L over a (spot_shift × vol_shift) grid."""
    import plotly.graph_objects as go

    if spot_shifts is None:
        spot_shifts = np.linspace(-0.30, 0.30, 31)
    if vol_shifts is None:
        vol_shifts = np.linspace(-0.10, 0.10, 21)

    Z = stress_grid(strategy, spot, T, spot_shifts, vol_shifts,
                    days_passed=days_passed, r=r, sigma=sigma)

    # x labels in percent, y labels in vol points
    x_labels = [f"{s*100:+.0f}%" for s in spot_shifts]
    y_labels = [f"{v:+.2f}" for v in vol_shifts]

    zmax = float(max(abs(Z.min()), abs(Z.max()))) or 1.0  # symmetric colorscale

    fig = go.Figure(go.Heatmap(
        z=Z,
        x=x_labels,
        y=y_labels,
        zmin=-zmax, zmax=zmax, zmid=0,
        colorscale=[
            [0.0, "#7f1d1d"],   # deep red
            [0.25, "#ef4444"],
            [0.5, "#1f2937"],   # near-zero blends into bg
            [0.75, "#22c55e"],
            [1.0, "#14532d"],   # deep green
        ],
        colorbar=dict(
            title=dict(text="P&L", font=dict(color="#9ca3af", size=12)),
            tickfont=dict(color="#9ca3af", size=11),
            outlinecolor="rgba(75,85,99,0.4)",
            outlinewidth=1,
        ),
        hovertemplate=("Spot shift %{x}<br>Vol shift %{y}<br>P&L %{z:+.2f}<extra></extra>"),
    ))

    sub = f"Spot = {spot:g}, T = {T:.3f}y, σ = {sigma:.2%}"
    if days_passed:
        sub += f", +{days_passed:g} days passed"
    fig.update_layout(
        title=dict(
            text=f"<b>{title}</b><br><span style='font-size:13px;color:#9ca3af'>{sub}</span>",
            font=dict(size=22, family="Inter, system-ui, sans-serif", color="#e5e7eb"),
            x=0.02, xanchor="left", y=0.95,
        ),
        xaxis=dict(
            title=dict(text="Spot shift", font=dict(size=14, color="#9ca3af")),
            tickfont=dict(size=11, color="#9ca3af"),
        ),
        yaxis=dict(
            title=dict(text="Vol shift (absolute)", font=dict(size=14, color="#9ca3af")),
            tickfont=dict(size=11, color="#9ca3af"),
        ),
        plot_bgcolor="#0b1020", paper_bgcolor="#0b1020",
        font=dict(family="Inter, system-ui, sans-serif", color="#e5e7eb"),
        margin=dict(l=80, r=40, t=110, b=70),
    )
    return fig

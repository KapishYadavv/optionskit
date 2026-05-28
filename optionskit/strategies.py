"""Build multi-leg European option strategies and visualize their payoff."""

from __future__ import annotations
from dataclasses import dataclass
from typing import Literal

import numpy as np


@dataclass
class Leg:
    kind: Literal["call", "put", "stock"]
    strike: float  # for stock: entry price
    premium: float  # for stock: 0.0 (no premium)
    qty: float = 1.0

    @property
    def label(self) -> str:
        side = "Long" if self.qty > 0 else "Short"
        if self.kind == "stock":
            return f"{side} Stock @ {self.strike:g}"
        return f"{side} {self.kind.title()}: {self.strike:g}"


class Strategy:
    """A collection of European option (and stock) legs you can price and plot."""

    def __init__(self) -> None:
        self.legs: list[Leg] = []

    def add_call(self, strike: float, premium: float, qty: float = 1) -> "Strategy":
        self.legs.append(Leg("call", strike, premium, qty))
        return self

    def add_put(self, strike: float, premium: float, qty: float = 1) -> "Strategy":
        self.legs.append(Leg("put", strike, premium, qty))
        return self

    def add_stock(self, entry: float, qty: float = 1) -> "Strategy":
        """Add a long (qty>0) or short (qty<0) stock leg at the given entry price."""
        self.legs.append(Leg("stock", entry, 0.0, qty))
        return self

    def payoff(self, prices) -> np.ndarray:
        """P&L at expiry across an array of underlying prices."""
        if not self.legs:
            raise ValueError("Strategy has no legs. Add one with add_call/add_put/add_stock.")
        prices = np.asarray(prices, dtype=float)
        total = np.zeros_like(prices)
        for leg in self.legs:
            if leg.kind == "call":
                payoff = np.maximum(prices - leg.strike, 0.0) - leg.premium
            elif leg.kind == "put":
                payoff = np.maximum(leg.strike - prices, 0.0) - leg.premium
            else:  # stock
                payoff = prices - leg.strike
            total += leg.qty * payoff
        return total

    # ------------------------------------------------------------------
    # Analytics helpers (used by the plot)
    # ------------------------------------------------------------------
    def breakevens(self, prices, pnl) -> list[float]:
        """Linearly-interpolated zero crossings of the payoff curve."""
        prices = np.asarray(prices, dtype=float)
        pnl = np.asarray(pnl, dtype=float)
        crossings: list[float] = []
        signs = np.sign(pnl)
        for i in range(len(pnl) - 1):
            if signs[i] == 0:
                crossings.append(float(prices[i]))
            elif signs[i] * signs[i + 1] < 0:
                x0, x1 = prices[i], prices[i + 1]
                y0, y1 = pnl[i], pnl[i + 1]
                crossings.append(float(x0 - y0 * (x1 - x0) / (y1 - y0)))
        # dedupe near-equal values
        unique: list[float] = []
        for x in crossings:
            if not unique or abs(x - unique[-1]) > 1e-6:
                unique.append(x)
        return unique

    def _extrema(self, prices, pnl) -> dict:
        """Identify max profit / max loss, marking edge-touching extremes as unbounded."""
        n = len(prices)
        i_max = int(np.argmax(pnl))
        i_min = int(np.argmin(pnl))

        def at_edge(i: int) -> bool:
            return i <= 1 or i >= n - 2

        return {
            "max_profit": {
                "x": float(prices[i_max]),
                "y": float(pnl[i_max]),
                "unbounded": at_edge(i_max),
            },
            "max_loss": {
                "x": float(prices[i_min]),
                "y": float(pnl[i_min]),
                "unbounded": at_edge(i_min),
            },
        }

    # ------------------------------------------------------------------
    # Plot
    # ------------------------------------------------------------------
    def plot_payoff(
        self,
        price_range=None,
        title: str = "Strategy payoff",
        show_breakevens: bool = True,
        show_extrema: bool = True,
    ):
        """Render the strategy P&L at expiry as a Plotly figure."""
        import plotly.graph_objects as go

        if not self.legs:
            raise ValueError("Strategy has no legs. Add one with add_call/add_put/add_stock.")

        refs = [leg.strike for leg in self.legs]
        if price_range is None:
            lo, hi = 0.7 * min(refs), 1.3 * max(refs)
        else:
            lo, hi = price_range
        prices = np.linspace(lo, hi, 600)
        pnl = self.payoff(prices)

        profit = np.where(pnl >= 0, pnl, 0.0)
        loss = np.where(pnl < 0, pnl, 0.0)

        fig = go.Figure()

        # Profit shading
        fig.add_trace(go.Scatter(
            x=prices, y=profit, mode="lines",
            line=dict(width=0),
            fill="tozeroy", fillcolor="rgba(34, 197, 94, 0.18)",
            hoverinfo="skip", showlegend=False,
        ))
        # Loss shading
        fig.add_trace(go.Scatter(
            x=prices, y=loss, mode="lines",
            line=dict(width=0),
            fill="tozeroy", fillcolor="rgba(239, 68, 68, 0.18)",
            hoverinfo="skip", showlegend=False,
        ))
        # Main payoff curve
        fig.add_trace(go.Scatter(
            x=prices, y=pnl, mode="lines",
            name="P&L at expiry",
            line=dict(color="#3b82f6", width=2.5),
            hovertemplate="Price %{x:.2f}<br>P&L %{y:+.2f}<extra></extra>",
        ))

        # Strike / entry markers
        for leg in self.legs:
            color = "#22c55e" if leg.qty > 0 else "#ef4444"
            fig.add_vline(
                x=leg.strike,
                line=dict(color=color, width=1.2, dash="dash"),
                opacity=0.7,
                annotation_text=leg.label,
                annotation_position="top",
                annotation=dict(
                    font=dict(size=12, color=color, family="Inter, system-ui, sans-serif"),
                    bgcolor="rgba(17, 24, 39, 0.85)",
                    bordercolor=color, borderwidth=1, borderpad=4,
                ),
            )

        # Breakeven dots + labels
        if show_breakevens:
            bes = self.breakevens(prices, pnl)
            if bes:
                fig.add_trace(go.Scatter(
                    x=bes, y=[0] * len(bes), mode="markers",
                    marker=dict(color="#fbbf24", size=10, line=dict(color="#0b1020", width=2),
                                symbol="circle"),
                    name="Breakeven",
                    hovertemplate="Breakeven %{x:.2f}<extra></extra>",
                    showlegend=False,
                ))
                for x in bes:
                    fig.add_annotation(
                        x=x, y=0, text=f"BE {x:.2f}",
                        showarrow=True, arrowhead=0, arrowcolor="rgba(251,191,36,0.6)",
                        ax=0, ay=30, yshift=-4,
                        font=dict(size=11, color="#fbbf24", family="Inter, system-ui, sans-serif"),
                        bgcolor="rgba(17, 24, 39, 0.85)",
                        bordercolor="#fbbf24", borderwidth=1, borderpad=3,
                    )

        # Max profit / max loss annotations
        if show_extrema:
            ext = self._extrema(prices, pnl)
            mp = ext["max_profit"]
            ml = ext["max_loss"]
            if not mp["unbounded"] and mp["y"] > 0:
                fig.add_annotation(
                    x=mp["x"], y=mp["y"],
                    text=f"Max Profit: {mp['y']:+.2f}",
                    showarrow=True, arrowhead=2, arrowcolor="#22c55e",
                    ax=0, ay=-40,
                    font=dict(size=12, color="#22c55e", family="Inter, system-ui, sans-serif"),
                    bgcolor="rgba(17, 24, 39, 0.9)",
                    bordercolor="#22c55e", borderwidth=1, borderpad=5,
                )
            elif mp["unbounded"] and mp["y"] > 0:
                fig.add_annotation(
                    x=mp["x"], y=mp["y"], text="Max Profit: Unlimited ↗",
                    showarrow=False, xanchor="right" if mp["x"] > (lo + hi) / 2 else "left",
                    yshift=-18,
                    font=dict(size=12, color="#22c55e", family="Inter, system-ui, sans-serif"),
                    bgcolor="rgba(17, 24, 39, 0.9)",
                    bordercolor="#22c55e", borderwidth=1, borderpad=5,
                )
            if not ml["unbounded"] and ml["y"] < 0:
                fig.add_annotation(
                    x=ml["x"], y=ml["y"],
                    text=f"Max Loss: {ml['y']:+.2f}",
                    showarrow=True, arrowhead=2, arrowcolor="#ef4444",
                    ax=0, ay=40,
                    font=dict(size=12, color="#ef4444", family="Inter, system-ui, sans-serif"),
                    bgcolor="rgba(17, 24, 39, 0.9)",
                    bordercolor="#ef4444", borderwidth=1, borderpad=5,
                )
            elif ml["unbounded"] and ml["y"] < 0:
                fig.add_annotation(
                    x=ml["x"], y=ml["y"], text="Max Loss: Unlimited ↘",
                    showarrow=False, xanchor="left" if ml["x"] < (lo + hi) / 2 else "right",
                    yshift=18,
                    font=dict(size=12, color="#ef4444", family="Inter, system-ui, sans-serif"),
                    bgcolor="rgba(17, 24, 39, 0.9)",
                    bordercolor="#ef4444", borderwidth=1, borderpad=5,
                )

        fig.update_layout(
            title=dict(
                text=f"<b>{title}</b>",
                font=dict(size=22, family="Inter, system-ui, sans-serif", color="#e5e7eb"),
                x=0.02, xanchor="left", y=0.95,
            ),
            xaxis=dict(
                title=dict(text="Underlying price at expiry", font=dict(size=14, color="#9ca3af")),
                tickfont=dict(size=12, color="#9ca3af"),
                gridcolor="rgba(75, 85, 99, 0.25)", zeroline=False,
            ),
            yaxis=dict(
                title=dict(text="Profit / Loss", font=dict(size=14, color="#9ca3af")),
                tickfont=dict(size=12, color="#9ca3af"),
                gridcolor="rgba(75, 85, 99, 0.25)",
                zeroline=True, zerolinecolor="rgba(156, 163, 175, 0.6)", zerolinewidth=1,
            ),
            plot_bgcolor="#0b1020", paper_bgcolor="#0b1020",
            font=dict(family="Inter, system-ui, sans-serif", color="#e5e7eb"),
            margin=dict(l=70, r=40, t=90, b=70),
            hovermode="x unified",
            hoverlabel=dict(bgcolor="#111827", bordercolor="#3b82f6",
                            font=dict(size=12, color="#e5e7eb")),
            showlegend=False,
        )
        fig.update_xaxes(showspikes=True, spikecolor="rgba(156,163,175,0.4)",
                         spikethickness=1, spikemode="across")
        return fig

    def save_payoff(self, path: str, **plot_kwargs) -> str:
        """Render and save the payoff chart.

        Extension drives the format:
        - ``.html`` → standalone interactive page (no extra deps)
        - ``.png`` / ``.jpg`` / ``.jpeg`` / ``.svg`` / ``.pdf`` → static export (requires ``kaleido``)
        """
        fig = self.plot_payoff(**plot_kwargs)
        ext = path.lower().rsplit(".", 1)[-1]
        if ext == "html":
            fig.write_html(path, include_plotlyjs="cdn", full_html=True)
        elif ext in {"png", "jpg", "jpeg", "svg", "pdf", "webp"}:
            fig.write_image(path)  # needs kaleido
        else:
            raise ValueError(f"Unsupported export extension: .{ext}")
        return path

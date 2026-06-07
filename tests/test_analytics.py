import math

import pytest

from optionskit import Strategy, presets, delta as bs_delta


# ---------- portfolio greeks ----------

def test_single_call_greeks_match_scalar():
    s = Strategy().add_call(100, premium=5, qty=1)
    g = s.greeks(spot=100, T=1.0, r=0.05, sigma=0.20)
    assert g["delta"] == pytest.approx(bs_delta(100, 100, 1.0, 0.05, 0.20, "call"))


def test_qty_scales_greeks():
    one = Strategy().add_call(100, premium=5, qty=1).greeks(100, 1.0, 0.05, 0.20)
    three = Strategy().add_call(100, premium=5, qty=3).greeks(100, 1.0, 0.05, 0.20)
    assert three["delta"] == pytest.approx(3 * one["delta"])
    assert three["vega"] == pytest.approx(3 * one["vega"])


def test_stock_adds_delta_only():
    s = Strategy().add_stock(entry=100, qty=1)
    g = s.greeks(spot=100, T=0.5, r=0.0, sigma=0.20)
    assert g["delta"] == pytest.approx(1.0)
    assert g["gamma"] == 0.0 and g["vega"] == 0.0 and g["theta"] == 0.0


def test_iron_condor_delta_small_at_center():
    c = presets.iron_condor(80, 90, 110, 120, 0.5, 2.0, 2.0, 0.5)
    g = c.greeks(spot=100, T=45 / 365, r=0.0, sigma=0.22)
    assert abs(g["delta"]) < 0.15  # roughly delta-neutral at the center


# ---------- summary ----------

def test_summary_iron_condor():
    c = presets.iron_condor(80, 90, 110, 120, 0.5, 2.0, 2.0, 0.5)
    s = c.summary()
    assert s["max_profit"] == pytest.approx(3.0, abs=1e-6)
    assert s["max_loss"] == pytest.approx(-7.0, abs=1e-6)
    assert len(s["breakevens"]) == 2
    assert s["breakevens"][0] == pytest.approx(87.0, abs=0.1)
    assert s["breakevens"][1] == pytest.approx(113.0, abs=0.1)
    assert s["net_premium"] == pytest.approx(-3.0)  # net credit
    assert s["risk_reward"] == pytest.approx(7.0 / 3.0, abs=1e-3)


def test_summary_long_call_unbounded_profit():
    s = Strategy().add_call(100, premium=5, qty=1).summary()
    assert s["max_profit"] == math.inf
    assert s["max_loss"] == pytest.approx(-5.0)
    assert s["breakevens"][0] == pytest.approx(105.0, abs=0.1)
    assert s["risk_reward"] is None


def test_summary_short_call_unbounded_loss():
    s = Strategy().add_call(100, premium=5, qty=-1).summary()
    assert s["max_loss"] == -math.inf
    assert s["max_profit"] == pytest.approx(5.0)


# ---------- probability of profit ----------

def test_pop_long_call_matches_closed_form():
    # POP = P(S_T > breakeven) under lognormal
    s = Strategy().add_call(100, premium=5, qty=1)
    pop = s.pop(spot=100, T=0.5, r=0.0, sigma=0.20)
    assert pop == pytest.approx(0.339, abs=0.01)


def test_pop_between_zero_and_one():
    c = presets.iron_condor(80, 90, 110, 120, 0.5, 2.0, 2.0, 0.5)
    pop = c.pop(spot=100, T=45 / 365, sigma=0.22)
    assert 0.0 < pop < 1.0


def test_pop_short_strategy_high():
    # A wide short strangle should have a high probability of profit
    s = Strategy().add_call(130, premium=1, qty=-1).add_put(70, premium=1, qty=-1)
    assert s.pop(spot=100, T=30 / 365, sigma=0.20) > 0.8


# ---------- time decay plot ----------

def test_plot_time_decay_returns_figure():
    import plotly.graph_objects as go

    s = presets.straddle(100, 4, 4, qty=1)
    fig = s.plot_time_decay(T=60 / 365, sigma=0.25)
    assert isinstance(fig, go.Figure)
    assert len(fig.data) >= 2  # multiple snapshots


def test_plot_time_decay_custom_snapshots():
    s = Strategy().add_call(100, premium=5, qty=1)
    fig = s.plot_time_decay(T=60 / 365, days_to_expiry=[60, 30, 0], sigma=0.2)
    assert len(fig.data) == 3

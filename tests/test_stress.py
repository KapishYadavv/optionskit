import numpy as np
import pytest

from optionskit import Strategy, presets, stress


def test_zero_shock_matches_current_mark():
    s = Strategy().add_call(strike=100, premium=5, qty=1)
    out = s.stress_test(spot=100, T=0.5, sigma=0.20,
                        scenarios=[{"spot_shift": 0, "vol_shift": 0, "days_passed": 0}])
    # PnL vs baseline must be ~0 (same market state)
    assert out[0]["pnl_vs_baseline"] == pytest.approx(0.0, abs=1e-9)


def test_long_call_profits_on_up_shock():
    s = Strategy().add_call(strike=100, premium=5, qty=1)
    out = s.stress_test(spot=100, T=0.5, sigma=0.20,
                        scenarios=[{"spot_shift": +0.20, "vol_shift": 0, "days_passed": 0}])
    assert out[0]["pnl"] > 5.0  # well in the money


def test_short_strangle_hurt_by_crash_and_vol_pop():
    s = Strategy().add_call(110, premium=2, qty=-1).add_put(90, premium=2, qty=-1)
    baseline = s.stress_test(100, 0.25, sigma=0.20,
                             scenarios=[{}])[0]["pnl"]
    crashed = s.stress_test(100, 0.25, sigma=0.20,
                            scenarios=[{"spot_shift": -0.15, "vol_shift": +0.10}])[0]["pnl"]
    # Short strangle suffers in a crash + vol spike
    assert crashed < baseline


def test_theta_helps_a_short_premium_seller():
    s = Strategy().add_call(110, premium=2, qty=-1).add_put(90, premium=2, qty=-1)
    no_time = s.stress_test(100, 30/365, sigma=0.20,
                            scenarios=[{}])[0]["pnl"]
    later = s.stress_test(100, 30/365, sigma=0.20,
                          scenarios=[{"days_passed": 14}])[0]["pnl"]
    assert later > no_time  # theta decay benefits the seller


def test_stress_grid_shape_and_center():
    s = Strategy().add_call(100, premium=5, qty=1)
    spot_shifts = np.linspace(-0.1, 0.1, 5)
    vol_shifts = np.linspace(-0.05, 0.05, 3)
    Z = stress.stress_grid(s, spot=100, T=0.5,
                           spot_shifts=spot_shifts, vol_shifts=vol_shifts,
                           sigma=0.20)
    assert Z.shape == (3, 5)
    # Right edge (positive spot shift) should beat left edge for a long call
    assert Z[:, -1].mean() > Z[:, 0].mean()


def test_plot_stress_heatmap_returns_figure():
    import plotly.graph_objects as go
    s = presets.iron_condor(80, 90, 110, 120, 0.5, 2.0, 2.0, 0.5)
    fig = s.plot_stress_heatmap(spot=100, T=30/365, sigma=0.22)
    assert isinstance(fig, go.Figure)
    # Heatmap trace present
    assert any(t.type == "heatmap" for t in fig.data)


def test_invalid_T_raises():
    s = Strategy().add_call(100, premium=5, qty=1)
    with pytest.raises(ValueError, match="T must be > 0"):
        s.stress_test(spot=100, T=0, sigma=0.20, scenarios=[{}])

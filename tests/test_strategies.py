import numpy as np
import pytest

from optionskit import Strategy


def test_long_call_hockey_stick():
    s = Strategy().add_call(strike=100, premium=5, qty=1)
    prices = np.array([80, 100, 105, 120])
    pnl = s.payoff(prices)
    # Below strike: -premium. At strike: -premium. Above: (S-K)-premium.
    np.testing.assert_allclose(pnl, [-5, -5, 0, 15])


def test_short_strangle_max_profit_between_strikes():
    s = Strategy()
    s.add_call(110, premium=2, qty=-1)
    s.add_put(90, premium=2, qty=-1)
    # Between the strikes both options expire worthless -> profit = sum of premiums
    assert s.payoff(np.array([100]))[0] == pytest.approx(4.0)
    # Far out of either side -> losing money
    assert s.payoff(np.array([60]))[0] < 0
    assert s.payoff(np.array([140]))[0] < 0


def test_plot_payoff_returns_plotly_figure():
    import plotly.graph_objects as go

    s = Strategy().add_call(100, premium=3, qty=1).add_put(90, premium=2, qty=-1)
    fig = s.plot_payoff()
    assert isinstance(fig, go.Figure)
    # Curve + two shading traces
    assert len(fig.data) >= 3
    # Strike annotations should mention both legs
    texts = " ".join(ann.text for ann in fig.layout.annotations)
    assert "Long Call: 100" in texts
    assert "Short Put: 90" in texts


def test_empty_strategy_raises():
    with pytest.raises(ValueError):
        Strategy().payoff([100])


def test_stock_leg_linear_payoff():
    s = Strategy().add_stock(entry=100, qty=1)
    np.testing.assert_allclose(s.payoff(np.array([80, 100, 120])), [-20, 0, 20])


def test_breakevens_long_call():
    s = Strategy().add_call(strike=100, premium=5, qty=1)
    prices = np.linspace(70, 130, 1001)
    pnl = s.payoff(prices)
    bes = s.breakevens(prices, pnl)
    assert len(bes) == 1
    assert bes[0] == pytest.approx(105.0, abs=0.1)


def test_breakevens_short_strangle():
    s = Strategy().add_call(110, premium=2, qty=-1).add_put(90, premium=2, qty=-1)
    prices = np.linspace(50, 150, 2001)
    pnl = s.payoff(prices)
    bes = s.breakevens(prices, pnl)
    assert len(bes) == 2
    assert bes[0] == pytest.approx(86.0, abs=0.1)
    assert bes[1] == pytest.approx(114.0, abs=0.1)


def test_save_payoff_html(tmp_path):
    s = Strategy().add_call(100, premium=5, qty=1)
    out = tmp_path / "chart.html"
    s.save_payoff(str(out))
    assert out.exists() and out.stat().st_size > 0

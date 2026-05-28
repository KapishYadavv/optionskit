import numpy as np
import pytest

from optionskit import presets


def test_straddle_min_at_strike():
    s = presets.straddle(strike=100, call_premium=5, put_premium=5, qty=1)
    # At the strike, both options expire worthless → max loss = total premium
    assert s.payoff(np.array([100]))[0] == pytest.approx(-10.0)
    # Far moves recover the premium and then some
    assert s.payoff(np.array([130]))[0] == pytest.approx(20.0)


def test_bull_call_spread_capped_profit_and_loss():
    s = presets.bull_call_spread(
        long_strike=100, long_premium=6,
        short_strike=110, short_premium=2,
        qty=1,
    )
    # Max loss = net debit = 4 below long strike
    assert s.payoff(np.array([90]))[0] == pytest.approx(-4.0)
    # Max profit = width - debit = 10 - 4 = 6 above short strike
    assert s.payoff(np.array([120]))[0] == pytest.approx(6.0)


def test_iron_condor_profit_inside_body():
    s = presets.iron_condor(
        put_long_strike=80,   put_long_premium=0.5,
        put_short_strike=90,  put_short_premium=2.0,
        call_short_strike=110, call_short_premium=2.0,
        call_long_strike=120, call_long_premium=0.5,
    )
    # Inside the body: net credit = (2 - 0.5) + (2 - 0.5) = 3
    assert s.payoff(np.array([100]))[0] == pytest.approx(3.0)
    # Beyond a wing: capped loss
    assert s.payoff(np.array([70]))[0] == pytest.approx(-7.0)
    assert s.payoff(np.array([130]))[0] == pytest.approx(-7.0)


def test_covered_call_caps_upside():
    s = presets.covered_call(stock_entry=100, call_strike=110, call_premium=3, qty=1)
    # Below the call strike: stock P&L + premium kept
    assert s.payoff(np.array([100]))[0] == pytest.approx(3.0)
    # Above the call strike: capped at (strike - entry) + premium = 10 + 3 = 13
    assert s.payoff(np.array([150]))[0] == pytest.approx(13.0)


def test_strangle_validation():
    with pytest.raises(ValueError):
        presets.strangle(put_strike=110, call_strike=100,
                         put_premium=1, call_premium=1)


def test_butterfly_symmetric():
    s = presets.butterfly(90, 100, 110,
                          low_premium=11, mid_premium=5, high_premium=1,
                          kind="call")
    # Max profit at the middle strike
    p = s.payoff(np.array([90, 100, 110]))
    assert p[1] > p[0] and p[1] > p[2]

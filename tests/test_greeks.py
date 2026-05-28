import pytest

from optionskit import black_scholes, delta, gamma


def test_atm_call_delta_above_half():
    d = delta(100, 100, 1, 0.05, 0.2, kind="call")
    assert 0.5 < d < 0.75


def test_put_call_delta_relation():
    # delta_call - delta_put == 1
    c = delta(100, 100, 1, 0.05, 0.2, "call")
    p = delta(100, 100, 1, 0.05, 0.2, "put")
    assert c - p == pytest.approx(1.0, abs=1e-9)


def test_gamma_matches_numerical_derivative():
    S, K, T, r, sigma = 100, 100, 1, 0.05, 0.2
    h = 0.01
    d_up = delta(S + h, K, T, r, sigma, "call")
    d_dn = delta(S - h, K, T, r, sigma, "call")
    numerical = (d_up - d_dn) / (2 * h)
    assert gamma(S, K, T, r, sigma) == pytest.approx(numerical, abs=1e-4)


def test_delta_matches_numerical_price_derivative():
    S, K, T, r, sigma = 100, 100, 1, 0.05, 0.2
    h = 0.01
    up = black_scholes(S + h, K, T, r, sigma, "call")
    dn = black_scholes(S - h, K, T, r, sigma, "call")
    numerical = (up - dn) / (2 * h)
    assert delta(S, K, T, r, sigma, "call") == pytest.approx(numerical, abs=1e-4)

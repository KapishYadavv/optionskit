import math

import pytest

from optionskit import black_scholes, delta, gamma, vega, theta, rho, greeks


# ---------- delta ----------

def test_atm_call_delta_above_half():
    d = delta(100, 100, 1, 0.05, 0.2, kind="call")
    assert 0.5 < d < 0.75


def test_put_call_delta_relation():
    c = delta(100, 100, 1, 0.05, 0.2, "call")
    p = delta(100, 100, 1, 0.05, 0.2, "put")
    assert c - p == pytest.approx(1.0, abs=1e-9)


def test_delta_matches_numerical_price_derivative():
    S, K, T, r, sigma = 100, 100, 1, 0.05, 0.2
    h = 0.01
    up = black_scholes(S + h, K, T, r, sigma, "call")
    dn = black_scholes(S - h, K, T, r, sigma, "call")
    assert delta(S, K, T, r, sigma, "call") == pytest.approx((up - dn) / (2 * h), abs=1e-4)


# ---------- gamma ----------

def test_gamma_matches_numerical_derivative():
    S, K, T, r, sigma = 100, 100, 1, 0.05, 0.2
    h = 0.01
    d_up = delta(S + h, K, T, r, sigma, "call")
    d_dn = delta(S - h, K, T, r, sigma, "call")
    assert gamma(S, K, T, r, sigma) == pytest.approx((d_up - d_dn) / (2 * h), abs=1e-4)


# ---------- vega ----------

def test_vega_call_equals_put():
    args = (100, 100, 1, 0.05, 0.2)
    assert vega(*args) == pytest.approx(vega(*args), abs=1e-12)


def test_vega_matches_numerical_derivative():
    S, K, T, r, sigma = 100, 100, 1, 0.05, 0.2
    h = 1e-4
    up = black_scholes(S, K, T, r, sigma + h, "call")
    dn = black_scholes(S, K, T, r, sigma - h, "call")
    assert vega(S, K, T, r, sigma) == pytest.approx((up - dn) / (2 * h), abs=1e-3)


def test_vega_per_percent_scaling():
    args = (100, 100, 1, 0.05, 0.2)
    assert vega(*args, per_percent=True) == pytest.approx(vega(*args) / 100.0)


# ---------- theta ----------

def test_theta_call_negative_for_atm():
    # ATM calls lose value as time passes
    assert theta(100, 100, 1, 0.05, 0.2, "call") < 0


def test_theta_matches_numerical_derivative():
    # Theta = ∂P/∂(−T) → numerical: -(P(T+h) − P(T−h)) / (2h)
    S, K, T, r, sigma = 100, 100, 1, 0.05, 0.2
    h = 1e-4
    up = black_scholes(S, K, T + h, r, sigma, "call")
    dn = black_scholes(S, K, T - h, r, sigma, "call")
    numerical = -(up - dn) / (2 * h)
    assert theta(S, K, T, r, sigma, "call") == pytest.approx(numerical, abs=1e-2)


def test_theta_per_day_scaling():
    args = (100, 100, 1, 0.05, 0.2)
    assert theta(*args, kind="call", per_day=True) == pytest.approx(
        theta(*args, kind="call") / 365.0
    )


# ---------- rho ----------

def test_rho_call_positive_put_negative():
    assert rho(100, 100, 1, 0.05, 0.2, "call") > 0
    assert rho(100, 100, 1, 0.05, 0.2, "put") < 0


def test_rho_call_minus_put_identity():
    # ∂(C−P)/∂r = K * T * exp(−rT)  (from put-call parity)
    S, K, T, r, sigma = 110, 100, 0.5, 0.03, 0.25
    expected = K * T * math.exp(-r * T)
    diff = rho(S, K, T, r, sigma, "call") - rho(S, K, T, r, sigma, "put")
    assert diff == pytest.approx(expected, abs=1e-9)


def test_rho_matches_numerical_derivative():
    S, K, T, r, sigma = 100, 100, 1, 0.05, 0.2
    h = 1e-6
    up = black_scholes(S, K, T, r + h, sigma, "call")
    dn = black_scholes(S, K, T, r - h, sigma, "call")
    assert rho(S, K, T, r, sigma, "call") == pytest.approx((up - dn) / (2 * h), abs=1e-2)


# ---------- aggregate ----------

def test_greeks_dict_keys():
    g = greeks(100, 100, 1, 0.05, 0.2, kind="call")
    assert set(g) == {"delta", "gamma", "vega", "theta", "rho"}
    assert g["delta"] == pytest.approx(delta(100, 100, 1, 0.05, 0.2, "call"))
    assert g["theta"] == pytest.approx(theta(100, 100, 1, 0.05, 0.2, "call"))

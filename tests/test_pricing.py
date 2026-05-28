import pytest

from optionskit import black_scholes


def test_known_call_value():
    # Classic textbook reference: S=100, K=100, T=1, r=5%, sigma=20% -> call ~ 10.4506
    price = black_scholes(100, 100, 1, 0.05, 0.20, kind="call")
    assert price == pytest.approx(10.4506, abs=1e-3)


def test_known_put_value():
    price = black_scholes(100, 100, 1, 0.05, 0.20, kind="put")
    assert price == pytest.approx(5.5735, abs=1e-3)


def test_put_call_parity():
    S, K, T, r, sigma = 120, 100, 0.5, 0.03, 0.25
    c = black_scholes(S, K, T, r, sigma, "call")
    p = black_scholes(S, K, T, r, sigma, "put")
    # C - P == S - K*exp(-rT)
    import math
    assert c - p == pytest.approx(S - K * math.exp(-r * T), abs=1e-6)


def test_expired_returns_intrinsic():
    assert black_scholes(110, 100, 0, 0.05, 0.2, "call") == pytest.approx(10.0)
    assert black_scholes(90, 100, 0, 0.05, 0.2, "put") == pytest.approx(10.0)
    assert black_scholes(90, 100, 0, 0.05, 0.2, "call") == pytest.approx(0.0)


def test_invalid_kind():
    with pytest.raises(ValueError):
        black_scholes(100, 100, 1, 0.05, 0.2, kind="banana")

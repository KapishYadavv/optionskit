import pytest

from optionskit import black_scholes, implied_vol


@pytest.mark.parametrize("sigma_true", [0.05, 0.15, 0.25, 0.45, 0.80, 1.20])
@pytest.mark.parametrize("kind", ["call", "put"])
def test_round_trip(kind, sigma_true):
    S, K, T, r = 100, 110, 0.75, 0.04
    price = black_scholes(S, K, T, r, sigma_true, kind)
    iv = implied_vol(price, S, K, T, r, kind)
    assert iv == pytest.approx(sigma_true, abs=1e-6)


def test_round_trip_deep_itm_put():
    S, K, T, r, sigma = 70, 100, 1.0, 0.03, 0.30
    price = black_scholes(S, K, T, r, sigma, "put")
    assert implied_vol(price, S, K, T, r, "put") == pytest.approx(sigma, abs=1e-6)


def test_round_trip_deep_otm_call():
    S, K, T, r, sigma = 100, 150, 0.5, 0.02, 0.40
    price = black_scholes(S, K, T, r, sigma, "call")
    assert implied_vol(price, S, K, T, r, "call") == pytest.approx(sigma, abs=1e-6)


def test_below_intrinsic_raises():
    with pytest.raises(ValueError, match="below intrinsic"):
        implied_vol(0.10, S=120, K=100, T=1, r=0.05, kind="call")  # intrinsic ~ 24.88


def test_above_upper_bound_raises():
    with pytest.raises(ValueError, match="upper bound"):
        implied_vol(200.0, S=100, K=100, T=1, r=0.05, kind="call")  # upper = S = 100


def test_expired_raises():
    with pytest.raises(ValueError, match="T > 0"):
        implied_vol(5.0, S=100, K=100, T=0, r=0.05, kind="call")


def test_invalid_kind():
    with pytest.raises(ValueError, match="call.*put"):
        implied_vol(5.0, S=100, K=100, T=1, r=0.05, kind="banana")

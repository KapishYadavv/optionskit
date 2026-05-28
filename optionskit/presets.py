"""Ready-made multi-leg European option strategies.

Each function returns a :class:`~optionskit.strategies.Strategy` that you can
``.payoff(...)`` or ``.plot_payoff()`` directly.
"""

from __future__ import annotations

from .strategies import Strategy


def straddle(strike: float, call_premium: float, put_premium: float, qty: float = 1) -> Strategy:
    """Long (qty>0) or short (qty<0) straddle at a single strike."""
    return (
        Strategy()
        .add_call(strike, premium=call_premium, qty=qty)
        .add_put(strike, premium=put_premium, qty=qty)
    )


def strangle(
    put_strike: float,
    call_strike: float,
    put_premium: float,
    call_premium: float,
    qty: float = 1,
) -> Strategy:
    """Long or short strangle (OTM put + OTM call). qty<0 = short strangle."""
    if put_strike >= call_strike:
        raise ValueError("strangle requires put_strike < call_strike")
    return (
        Strategy()
        .add_put(put_strike, premium=put_premium, qty=qty)
        .add_call(call_strike, premium=call_premium, qty=qty)
    )


def bull_call_spread(
    long_strike: float,
    short_strike: float,
    long_premium: float,
    short_premium: float,
    qty: float = 1,
) -> Strategy:
    """Long lower-strike call + short higher-strike call. Debit spread."""
    if long_strike >= short_strike:
        raise ValueError("bull_call_spread requires long_strike < short_strike")
    return (
        Strategy()
        .add_call(long_strike, premium=long_premium, qty=qty)
        .add_call(short_strike, premium=short_premium, qty=-qty)
    )


def bear_put_spread(
    long_strike: float,
    short_strike: float,
    long_premium: float,
    short_premium: float,
    qty: float = 1,
) -> Strategy:
    """Long higher-strike put + short lower-strike put. Debit spread."""
    if long_strike <= short_strike:
        raise ValueError("bear_put_spread requires long_strike > short_strike")
    return (
        Strategy()
        .add_put(long_strike, premium=long_premium, qty=qty)
        .add_put(short_strike, premium=short_premium, qty=-qty)
    )


def iron_condor(
    put_long_strike: float,
    put_short_strike: float,
    call_short_strike: float,
    call_long_strike: float,
    put_long_premium: float,
    put_short_premium: float,
    call_short_premium: float,
    call_long_premium: float,
    qty: float = 1,
) -> Strategy:
    """Classic iron condor: long wings + short body. qty>0 = standard credit condor."""
    if not (put_long_strike < put_short_strike < call_short_strike < call_long_strike):
        raise ValueError(
            "iron_condor requires put_long < put_short < call_short < call_long"
        )
    return (
        Strategy()
        .add_put(put_long_strike, premium=put_long_premium, qty=qty)
        .add_put(put_short_strike, premium=put_short_premium, qty=-qty)
        .add_call(call_short_strike, premium=call_short_premium, qty=-qty)
        .add_call(call_long_strike, premium=call_long_premium, qty=qty)
    )


def covered_call(
    stock_entry: float,
    call_strike: float,
    call_premium: float,
    qty: float = 1,
) -> Strategy:
    """Long stock + short call (one contract per share-unit of qty)."""
    return (
        Strategy()
        .add_stock(stock_entry, qty=qty)
        .add_call(call_strike, premium=call_premium, qty=-qty)
    )


def protective_put(
    stock_entry: float,
    put_strike: float,
    put_premium: float,
    qty: float = 1,
) -> Strategy:
    """Long stock + long put (insurance)."""
    return (
        Strategy()
        .add_stock(stock_entry, qty=qty)
        .add_put(put_strike, premium=put_premium, qty=qty)
    )


def butterfly(
    low_strike: float,
    mid_strike: float,
    high_strike: float,
    low_premium: float,
    mid_premium: float,
    high_premium: float,
    kind: str = "call",
    qty: float = 1,
) -> Strategy:
    """Long butterfly: +1 / -2 / +1 around a center strike."""
    if not (low_strike < mid_strike < high_strike):
        raise ValueError("butterfly requires low < mid < high strikes")
    if kind not in ("call", "put"):
        raise ValueError("butterfly kind must be 'call' or 'put'")
    s = Strategy()
    leg = s.add_call if kind == "call" else s.add_put
    leg(low_strike, premium=low_premium, qty=qty)
    leg(mid_strike, premium=mid_premium, qty=-2 * qty)
    leg(high_strike, premium=high_premium, qty=qty)
    return s

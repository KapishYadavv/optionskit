# Bull call spread: long ITM/ATM call, short OTM call.
# Capped profit, capped loss — a cheaper bullish bet.

from optionskit import presets

s = presets.bull_call_spread(
    long_strike=100, long_premium=6.0,
    short_strike=110, short_premium=2.0,
    qty=1,
)

fig = s.plot_payoff(title="Bull Call Spread (100 / 110)")
fig.show()

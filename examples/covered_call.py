# Covered call: long 100 shares + short 1 OTM call.
# Collects premium; caps upside above the call strike.

from optionskit import presets

s = presets.covered_call(
    stock_entry=100,
    call_strike=110,
    call_premium=3.0,
    qty=1,
)

fig = s.plot_payoff(title="Covered Call (stock @ 100, short 110c)")
fig.show()

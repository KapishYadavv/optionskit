# Long straddle: buy a call AND a put at the same strike.
# Profits if the underlying moves big in either direction.

from optionskit import presets

s = presets.straddle(strike=100, call_premium=4.5, put_premium=4.0, qty=1)

fig = s.plot_payoff(title="Long Straddle @ 100")
fig.show()

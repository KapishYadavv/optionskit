#Long call: where we long a call option.

from optionskit import Strategy

s = Strategy().add_call(strike=100, premium=5, qty=1)

fig = s.plot_payoff(title="Long Call")
fig.show()

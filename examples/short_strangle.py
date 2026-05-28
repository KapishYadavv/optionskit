#Short strangle: where we sell an OTM call and an OTM put.

from optionskit import Strategy

s = Strategy()
s.add_call(18500, premium=120, qty=-1)
s.add_put(17500, premium=100, qty=-1)

fig = s.plot_payoff(title="Short Strangle")
fig.show()

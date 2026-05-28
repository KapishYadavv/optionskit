# Iron condor: short strangle + long wings.
# Defined risk, profits if the underlying stays inside the body.

from optionskit import presets

s = presets.iron_condor(
    put_long_strike=80,  put_long_premium=0.50,
    put_short_strike=90, put_short_premium=2.00,
    call_short_strike=110, call_short_premium=2.20,
    call_long_strike=120,  call_long_premium=0.60,
    qty=1,
)

fig = s.plot_payoff(title="Iron Condor (80 / 90 / 110 / 120)")
fig.show()

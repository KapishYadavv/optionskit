# Portfolio Greeks, summary stats, probability of profit, and time decay —
# everything OptionsKit can tell you about a position beyond the raw payoff.

from optionskit import presets

condor = presets.iron_condor(
    put_long_strike=80,    put_long_premium=0.50,
    put_short_strike=90,   put_short_premium=2.00,
    call_short_strike=110, call_short_premium=2.20,
    call_long_strike=120,  call_long_premium=0.60,
)

spot, T, sigma = 100, 45 / 365, 0.22

print("Summary:")
for k, v in condor.summary().items():
    print(f"  {k:14} {v}")

print("\nNet Greeks:")
for k, v in condor.greeks(spot, T, sigma=sigma).items():
    print(f"  {k:6} {v:+.4f}")

print(f"\nProbability of profit: {condor.pop(spot, T, sigma=sigma):.1%}")

# Time-decay overlay: see how the value curve melts toward the expiry payoff.
fig = condor.plot_time_decay(T=T, sigma=sigma, title="Iron Condor — Time Decay")
fig.show()

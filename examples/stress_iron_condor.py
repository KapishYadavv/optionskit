# Stress test an iron condor: how much pain under various market shocks?
#
# Scenarios include a -10% crash, a vol spike, a slow grind, etc.
# The heatmap then shows P&L across a full (spot shift × vol shift) grid.

from optionskit import presets

condor = presets.iron_condor(
    put_long_strike=80,    put_long_premium=0.50,
    put_short_strike=90,   put_short_premium=2.00,
    call_short_strike=110, call_short_premium=2.20,
    call_long_strike=120,  call_long_premium=0.60,
)

# Single-shot scenarios — quick "what if?" answers.
scenarios = [
    {"spot_shift": 0.00,  "vol_shift":  0.00, "days_passed":  0},   # baseline
    {"spot_shift": -0.10, "vol_shift": +0.05, "days_passed":  7},   # -10% crash + vol pop + a week
    {"spot_shift": -0.20, "vol_shift": +0.15, "days_passed":  1},   # Black-Monday-style
    {"spot_shift": +0.05, "vol_shift": -0.02, "days_passed": 14},   # gentle drift + vol crush
    {"spot_shift":  0.00, "vol_shift":  0.00, "days_passed": 21},   # 3 weeks of theta with no move
]

results = condor.stress_test(spot=100, T=45/365, sigma=0.22, scenarios=scenarios)
for row in results:
    print(f"  spot {row['spot_shift']:+.2%}  vol {row['vol_shift']:+.2f}  "
          f"+{row['days_passed']:>2.0f}d   P&L = {row['pnl']:+.2f}")

# Heatmap across the full surface.
fig = condor.plot_stress_heatmap(
    spot=100, T=45/365, sigma=0.22, days_passed=0,
    title="Iron Condor — Stress Test",
)
fig.show()

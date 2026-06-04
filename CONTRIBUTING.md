# Contributing to OptionsKit

First off, Thanks for your interest. OptionsKit is small, focused, and friendly to new contributors. This guide tells you how to get set up and what we look for in a PR.

## TL;DR

```bash
git clone https://github.com/KapishYadavv/optionskit
cd optionskit
python -m pip install -e ".[dev]"
pytest
```

If `pytest` is green, you're ready to hack!

## Use of AI

- Please only use AI IF you have domain understanding of financial and options markets as AI struggles greatly with fintech tasks which require both technical and domain depth.
- Do NOT blind accept AI edits for domain related tasks.

## Project layout

```
optionskit/
├── pricing.py     # Black-Scholes for European calls/puts
├── greeks.py      # delta, gamma, vega, theta, rho (+ greeks() dict)
├── iv.py          # implied volatility solver (Brent's method)
├── strategies.py  # Strategy class, payoff math, plot_payoff (Plotly)
├── presets.py     # straddle, iron_condor, covered_call, ...
└── __init__.py    # public API surface
tests/             # one file per module, ~50 tests total
examples/          # runnable scripts you can `python examples/<name>.py`
```

Each module owns one job. If something doesn't fit, it usually means a new module — not a bigger one.

## Design principles

- **API > features.** A clean five-line example beats an extra parameter.
- **Defaults should be sensible.** A user shouldn't need to look up the docs for the common case.
- **No silent NaN.** Bad inputs raise `ValueError` with an actionable message (see `iv.py` for the pattern).
- **European options only.** American, exotic, and Monte-Carlo pricing are out of scope. We may revisit later.
- **Plotly only for visualization.** No matplotlib, no Bokeh. Keep the dep surface tight.

## How to add a new feature

### A new strategy preset

1. Add a function to `optionskit/presets.py` that returns a `Strategy`. Validate inputs (e.g. strike ordering) and raise `ValueError` with a clear message.
2. Add a test in `tests/test_presets.py` — check at least one known-payoff point.
3. Add a runnable demo to `examples/`.
4. Export nothing extra from `__init__.py` — presets are accessed as `optionskit.presets.your_preset(...)`.

### A new Greek or pricing model

1. Add closed-form math to `greeks.py` or `pricing.py`. Share `_d1_d2` if you need it.
2. Add a test that compares to a numerical derivative of `black_scholes` (see existing `test_*_matches_numerical_derivative` patterns).
3. If it's a Greek, add it to the `greeks(...)` aggregate dict.
4. Export from `__init__.py`.

### A plot tweak

`Strategy.plot_payoff` in `strategies.py` is one function on purpose — easy to skim end-to-end. If you're adding a marker / annotation type, keep it behind a boolean flag (`show_breakevens=True` is the pattern) so existing call sites don't break.

## Code style

- **Formatter / linter:** [`ruff`](https://docs.astral.sh/ruff/) — `ruff check .` should be clean before you push.
- **Line length:** 100.
- **Type hints:** add them on new public functions. Existing untyped signatures are tech debt we're chipping away at — adding hints to old code is welcome.
- **Docstrings:** every public function gets one. Cover units, return type, and any raised exceptions. See `greeks.theta` for the level of detail.
- **No new runtime dependencies** without a discussion (open an issue first). Dev-only deps are fine to add.

## Tests

We use `pytest`. A PR without a test for new behavior will likely be asked to add one.

```bash
pytest                  # run everything
pytest tests/test_iv.py -v   # one file, verbose
pytest -k strangle      # by name substring
```

Aim for tests that describe *behavior* (`test_iron_condor_profit_inside_body`), not implementation. Use known-value tests for math, parity identities for cross-checks, and numerical derivatives for Greeks.

## PR process

1. Open an issue first for anything non-trivial.. it's faster than a rejected PR.
2. Fork → branch off `main` → keep the diff focused on one thing.
3. Make sure `pytest` and `ruff check .` are both green.
4. Use present-tense, imperative commit messages: `add bear call spread preset`, not `added bear call spread preset`.
5. In the PR description, link the issue and explain the *why*, not just the *what*.
6. Be patient — this is maintained by one person.

## Reporting bugs

Open a GitHub issue with:
- OptionsKit version (`python -c "import optionskit; print(optionskit.__version__)"`)
- Python version + OS
- A minimum reproducible snippet (5–10 lines)
- What you expected vs what happened


## What's out of scope

To keep the library tight, we won't merge:
- Exotic options
- Trading signals, indicators, or strategy backtests
- Broker / exchange integrations
- Real-time data feeds
- GUI / dashboard frameworks

Most of these are better as a separate library that *uses* OptionsKit (especially exotic options).

## License

By contributing you agree your work is licensed under the [MIT License](LICENSE).

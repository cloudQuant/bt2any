# Indicator and data-line access

Load when: Read when the strategy uses indicators or custom data lines (funding/mark price).

## Python semantics
- Indicators are created in `__init__` via `bt.indicators.X(self.data, ...)` and become
  readable at bar T only after minperiod. Before that, `next()` is not called
  (`prenext()` runs instead).
- `self.data.close[0]` = current bar; `[1]` = previous bar. Same for custom lines:
  `self.data.current_funding_rate[1]` is the PREVIOUS bar's rate.
- Bollinger: `lines.mid/top/bot`; SMA has one line. Verify std convention (ddof)
  against the oracle before trusting band values.

## Target checklist
- [ ] indicator created in the framework start hook, not arbitrarily in constructor
- [ ] minperiod/warmup matched: first traded bar equals the oracle
- [ ] extra lines registered as named series; not dropped
- [ ] `[1]` semantics = previous completed bar (funding off-by-one is a top failure)

## Failure signature
If trades occur earlier/later than the oracle, check minperiod and NaN handling first.

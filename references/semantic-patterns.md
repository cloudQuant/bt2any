# Backtrader Semantic Patterns (language-agnostic)

Source-behavior notes that any target-language port must reproduce. These are about
what backtrader Python *does*, not about any target API.

## Timing and bar lifecycle

- `next()` runs once per bar after the bar is closed. Signals computed from the
  current bar's close are executed at the next bar's open (market order), unless
  `cheat_on_open` is enabled. Reproduce this one-bar execution lag.
- `prenext()` is called while any indicator's minperiod is not satisfied. The first
  `next()` happens when all indicators are ready. `bar_num` must count consistently
  with what the oracle counts (confirm from source/runner).
- `notify_order()` fires on status transitions (Submitted/Accepted/Completed/
  Canceled/Margin/Rejected). Only Completed with a fill changes position.
- `notify_trade()` fires with `trade.isclosed=True` when a position round-trip
  closes; use its `pnlcomm` (net of commission) for win/loss statistics.

## Orders

- Market orders: price is the next bar's open, not the signal bar's close.
- Limit/stop orders: must respect intrabar high/low ordering. A common simplification
  (`open → low → high → close`) systematically overstates grid-like strategies;
  match the target framework's actual fill model to the oracle's.
- Pending-order guard: do not submit a new order while one is pending unless the
  source explicitly allows it; otherwise trade counts diverge.
- `buy`/`sell` with `size` change position by that amount; `close()` closes the
  entire open position. Reverse (e.g. sell while long) first reduces then opens.
- Order role (open/close) must be carried with the order (e.g. `addinfo`), not
  inferred from the notification context.

## Indicators

- Create indicators in the framework's start hook, not the constructor, unless the
  target framework requires otherwise. Reproduce the source's minperiod.
- SMA/EMA/STD: confirm the exact formula and DDof (pandas std default ddof=1,
  backtrader uses population-style). A one-off in std changes Bollinger bands.
- `self.data.current_funding_rate[1]` means the previous bar. `[0]` is current.
  Off-by-one on this line is the most common cause of funding-parity failures.
- Rolling windows: reproduce warmup and NaN handling. An indicator that outputs NaN
  before minperiod must not trade early.

## Commission and funding

- `percabs=True` means a percentage commission is expressed as a decimal fraction
  (0.0004 = 0.04%), not percent units. Default differs across frameworks — set it.
- Funding: positive rate ⇒ longs pay, shorts receive. Value = rate × position size ×
  mark price × mult. Many backtrader forks settle on every bar using the *previous*
  bar's rate and mark price; verify against the source runner.
- `margin`/`stocklike`: stock-like mode makes equity include position market value;
  futures-like mode may only book margin, producing distorted drawdown. Match the
  oracle's mode exactly.

## Analyzers

- Sharpe: verify period/annualization and `riskfreerate`; the parameter name in the
  source may be `riskfreerate` (not `risk_free_rate`). Different annualization factors
  produce large apparent mismatches that are not strategy bugs.
- DrawDown: confirm whether it is reported in percent (e.g. 29.13) or fraction (0.2913).
- TradeAnalyzer counts include only closed trades; open trades at end are not counted.

## Data and resampling

- CSV datetime in backtest bundles may be `M/D/YYYY H:MM` (month first). Many target
  CSV parsers assume `YYYY-MM-DD`; parse explicitly with the source format.
- Extra columns (funding rate, mark price, volume metrics) must be registered as
  named data lines; a target that only reads OHLCV will silently drop the signal.
- Resample/replay can duplicate the tail bar or shift timestamps by one period.
  Confirm with the oracle's first and last processed timestamps.
- Multi-timeframe: a slow indicator must be read with the fast clock's current bar,
  avoiding look-ahead from a not-yet-closed slow bar.

## Feature caches / external models

If the Python runner precomputes a feature file (model predictions, third-party
normalization) and the target cannot reproduce it natively, the cached file is the
only acceptable external input — but it must be treated as data, not as an action
table. Replaying decisions from the oracle is not a conversion.

## Debugging mismatches

1. Compare `bar_num` and the first/last processed timestamps first — this catches
   feed/date parsing and minperiod errors early.
2. Compare trade counts before comparing PnL — count mismatches mean order logic,
   not arithmetic.
3. Only then compare equity; a constant ratio points to sizing/margin/commission,
   a growing divergence points to funding or compounding.
4. Log paired order/trade events from both sides (same columns) and diff them. Never
   edit the result JSON to force agreement.

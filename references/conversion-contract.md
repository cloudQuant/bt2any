# Conversion Contract

The single source of truth for what a converted strategy must produce. Applies to
all 16 target languages. Derived from the parity discipline of large-scale
backtrader porting (back_trader iter72), generalized away from any one framework.

## Result JSON schema

Both `py_result.json` (oracle, produced by the unmodified Python runner) and
`results/<lang>_result.json` (target) use exactly these 11 fields:

| Field | Meaning | Source in backtrader |
|---|---|---|
| `bar_num` | number of bars processed | len(data) observed by strategy |
| `buy_count` | number of buy orders | TradeAnalyzer `long.total` (or null) |
| `sell_count` | number of sell orders | TradeAnalyzer `short.total` (or null) |
| `win_count` | winning trades | TradeAnalyzer `won.total` (or null) |
| `loss_count` | losing trades | TradeAnalyzer `lost.total` (or null) |
| `trade_num` | closed trades | TradeAnalyzer `total.total` (or null) |
| `final_value` | ending broker value | broker.getvalue() |
| `sharpe_ratio` | SharpeRatio analyzer | analyzer value |
| `annual_return` | annualized return | analyzer value |
| `max_drawdown` | max drawdown percent | analyzer value |
| `return_rate` | return percent | (final/cash - 1) * 100 |

Rules:
- **Counts must come from the framework's trade analyzer**, not from counters you
  increment in `next()`. Self-counts are off-by-one around open trades.
- **`null` is not `0`.** If the oracle emits null for a count, emit null. Zero means
  "there were trades but zero of this kind"; null means "analyzer does not report it".
- Alias: `total_trades` is accepted as `trade_num` by the validator.

## Allowed extra keys

Benchmark/performance keys only:
`engine, rows, read_time_sec, run_time_sec, total_time_sec, process_wall_time_sec,
results_time_sec, strategy_function_time_sec, sum_profit`.

Any other extra key is a hard error (`rejected_field_error`). Do not add debug keys
to the result file — put diagnostics in a separate log.

## Tolerance

Parity passes when for every numeric field:

```
abs(target - oracle) <= 1e-6   OR   rel_diff <= 1e-6
```

- Non-finite handling: NaN vs NaN is equal; NaN vs number is a mismatch.
- Counts (integers) must match exactly; tolerance does not apply.
- Strings (if any) must match exactly.

## Config is the single source of truth

`config.yaml` owns: `cash`, `commission`, `mult`, `margin`, strategy params,
analyzer settings, data paths, and date ranges. Target code reads config at
startup. Never hardcode a value that the Python runner reads from config — the
two sides will drift.

## Evidence discipline

- The Python side is the oracle. Run it once, save `py_result.json`, then treat it
  as read-only.
- To prove parity you must **really run** the target and persist its result JSON.
  Static reasoning, "looks equivalent", or a checked checkbox is not acceptance.
- If a run fails 3 times on the same issue, stop and record `blocked_reason` with
  evidence. Do not lower the tolerance or edit the oracle.
- If the target framework is unavailable, mark the port `scaffold-only`; do not
  claim validation.

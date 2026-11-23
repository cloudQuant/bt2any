# Example: Analyzer parity (Sharpe / Returns / DrawDown / Trades)

Load when: the strategy's result includes Sharpe, annual return, max drawdown, or trade stats.

## Python facts to read from the source (not from a template)

- `bt.analyzers.SharpeRatio` parameters: `timeframe`, `compression`, `riskfreerate`,
  `factor`, `annualize`, `convrate`, `stddev_sample`. Note the parameter name is
  `riskfreerate` (no underscore between risk/free).
- `bt.analyzers.Returns` uses `period` for annualization (e.g. days=252).
- `DrawDown` reports percent (e.g. 29.13) — not fraction 0.2913.
- `TradeAnalyzer` buckets: `total.total`, `long.total`, `short.total`,
  `won.total`, `lost.total`. Counts are closed trades only.

## Mapping to the target

| Oracle field | Target source |
|---|---|
| `sharpe_ratio` | target Sharpe analyzer with the SAME period/riskfree/annualization |
| `annual_return` | target returns analyzer or `(final/cash)^(period/days)-1` |
| `max_drawdown` | target drawdown as PERCENT |
| `return_rate` | `(final/cash - 1) * 100` |
| counts | target trade analyzer buckets, null when the bucket is absent |

## Symptoms

- Sharpe differs but trades/equity match → analyzer parameter mismatch (most common:
  riskfree or annualization factor). Copy values from the source runner.
- max_drawdown off by ~100× → percent vs fraction.
- trade_num differs by 1 → open trade at end counted on one side only.

## Do NOT

- Do not fit an analyzer constant to make numbers agree.
- Do not emit extra analyzer keys in the result JSON (whitelist only).

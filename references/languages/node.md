# Target: Node.js

Status: **real-implementation based** (benchmark sample + `.iter72_lane_node/FMA_RECIPE.md`).
Read `languages/_implementation-notes.md` first.

## Verified routing — NOT ffi-napi

- Sample: `languages/node/bb_adx_strategy.js` (4.11 KB), `require("backtrader")`,
  default engine `node_swig_package`.
- C ABI route: hand-written **N-API + libffi plugin** `btffi.node` built by
  `bindings/c/adapter/node/ffi/build.sh` — **no npm/node-gyp/network**.
  `btffi.cc` (15.77 KB) → `btffi.node` (53.1 KB); JS facade
  `bindings/c/adapter/node/package/backtrader.js` does
  `require(process.env.BACK_TRADER_NODE_FFI || '../ffi/btffi.node')` with signatures
  from generated `signatures.json`. Runner `run_node_cabi_strategy_backtests.py`.
- SWIG route: `run_node_swig_strategy_backtests.py`, adapter
  `back_trader_swig_adapter.node/.so`.

## Real API mapping (sample)

| backtrader | Node facade |
|---|---|
| strategy | `class X extends bt.Strategy { init() {...} next() {...} }` |
| indicators | `bt.indicators.ADX(this.data,...)`, `bt.indicators.BollingerBands(this.data.close,...)` |
| data | `this.data.close[0]` (facade) / C ABI line reads via ffi |
| orders | `bt.Order.Stop`, `buy()/sell()/close()` wrappers |
| feed | `new bt.feeds.PandasData(dataPath, ...)` |
| run | `cerebro.adddata(...)`, `cerebro.run(engine)` |
| output | `writeResult(result, outputPath)` = `JSON.stringify(result,null,2)+"\n"` + stdout echo |

## Build / run (real commands)

`bindings/c/adapter/node/ffi/build.sh` (macOS):
```bash
g++ -std=c++17 -O1 -fPIC -shared -I"$INCLUDE" -DNAPI_VERSION=8 \
  -Wl,-undefined,dynamic_lookup -Wl,-rpath,"$FFI/lib" -I"$FFI/include" -L"$FFI/lib" \
  "$HERE/btffi.cc" -o "$HERE/btffi.node" -lffi
```
Linux adds `-Wl,--unresolved-symbols=ignore-all -ldl -lffi`. Node headers from
`node -p 'process.config.variables.node_prefix + "/include/node"'`, homebrew, etc.
```bash
python3 scripts/run_node_cabi_strategy_backtests.py \
  --build-dir build_iter54_lang15_strict --strategies-root strategies \
  --strategy <dir> --out-dir /tmp/node_run
```
Env: `BACK_TRADER_REPO_ROOT`, `BACK_TRADER_C_ABI_PATH`, `BACK_TRADER_NODE_PACKAGE`,
`BACK_TRADER_NODE_FFI`. Result `strategies/<dir>/results/node_result.json`.

## Node-specific pitfalls (highest-value lane facts)

- **FMA / bit-exactness is the most expensive pitfall**: core defaults
  `-ffp-contract=fast`; on arm64 EMA/MACD recurrences fuse into one `fma`. Naive JS
  `a*b+c` differs 1 ulp/step — 2939/4134 bars differed. Fix INSIDE the port with
  `doubleFma` (DataView/BigInt exact split + ties-to-even), call
  `doubleFma(prev, alpha1, cur*alpha)`; do not modify shared harness. Only fuse where
  C++ actually fuses (CPython two-rounding paths like `emaRsiVaStep` must not).
- Do not classify by ulp magnitude (`max_ulp` cancellation amplifies) — use
  seed-symmetry and `max_rel 1e-12..1e-16`.
- Engine CSV fast-path truncates fractional part to 18 digits — apply
  `engineParseDouble(csvNumber(v))` before writing float signal columns.
- `bt_node_harness.js` must be byte-identical (sha256
  `97bdf8d8c860c4c88cfc082944ba8b9e3090682650e7f839c082abaeff324eed`); an old fork
  had `ffi.alloc(8)` heap overflow. Each cell needs canonical harness + `<cell>.js`;
  `trend_following/0001_sma_trend_following` has no harness — do not copy it.
- 11-field contract, 1e-6 tolerance, counts exactly equal; win/loss from
  `tradeBuckets`, never self-counted. Never embed `py_result.json` numbers in port
  (static gate detects hardcoding).
- Copy pandas/backtrader quirks exactly: NaN propagation, dropna, rolling warm-up,
  `delta.where(delta>0,0)`, divide-by-zero → `+inf`, float summation order
  (harness provides `neumaierSum/pairwiseSum/numpyMean/naiveSum`).

## Result JSON

`writeResult()` = `JSON.stringify(result, null, 2) + "\n"`, `mkdirSync(recursive)`,
write `--output`, stdout echo. Fields: `engine, bar_num, buy_count, sell_count,
win_count, loss_count, sum_profit, read_time_sec, run_time_sec, total_time_sec,
sharpe_ratio, annual_return, max_drawdown, total_trades, return_rate, final_value`.

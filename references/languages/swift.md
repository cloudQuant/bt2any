# Target: Swift

Status: **real-implementation based** (benchmark sample + `会话13-swift技能提案.md` S1–S15).
Read `languages/_implementation-notes.md` first.

## Verified routing — two forms coexist

- Benchmark form: `import Backtrader` (SwiftPM package facade) with C ABI underneath
  via clang module `BackTraderC` (module map exposing four headers). Runner
  `run_swift_c_abi_strategy_backtests.py`.
- Legacy form: `import BackTraderC` (direct clang module) — a vendor tool
  (`vendor_legacy_compat.py`) rewrites it to `import Backtrader`.
- Sample: `languages/swift/bb_adx_strategy.swift` (5.04 KB); support TU
  `benchmarks/language_scripts/swift/Iter54SwiftSupport.swift` (79 KB).

## Real API mapping (sample)

| backtrader | Swift facade |
|---|---|
| strategy | `final class X: Strategy`, `override func start()`, `next()` |
| indicators | `adx = ADX(); adx.set_period(p); adx.add_data_source(0,"close"); bb = BollingerBands(); bb.set_bollinger_params(period,dev); addindicator(adx/bb)` |
| data | `data.close[0] / [-1]` |
| orders | `sell(Int32(0), 1.0)`, `buy(Int32(0), 1.0, stopPrice, OrderExecution.Stop)`, `self.close(0)` |
| order status | `order.getStatus()` vs `OrderNotification.Completed` |
| feed | `cerebro.add_pandas_csv_data_mapped(...)` |
| output | `benchmarkBenchmarkJson(rawJson:engine:...)`, `benchmarkWriteOutput(output,payload)`, `print(payload)` |

`@main struct XRunner` parses `--output`/`--engine` (default `swift`).

## Build / run (real commands)

```bash
swiftc -I <build>/c_package/include -L <build>/bindings/c -lback_trader_c_abi \
  -Xlinker -rpath -Xlinker <cabi_dir> \
  benchmarks/language_scripts/swift/Iter54SwiftSupport.swift <strategy>.swift \
  -o artifacts/iter54_swift/run/_bin/<strategy>/<strategy>_swift
<exe> --output <strategy>/results/swift_result.json --engine swift
```
Env `BACK_TRADER_REPO_ROOT`, `DYLD_LIBRARY_PATH`/`LD_LIBRARY_PATH` to `cabi_dir`.
C ABI lookup order `libback_trader_c_abi.dylib` → `.so` → `back_trader_c_abi.dll`.
Swift 6.x. Result `<strategy>/results/swift_result.json`.

## Swift-specific pitfalls (S1–S15, real)

- macOS has no `flock(1)` — use `fcntl.flock` shim; it MUST call
  `os.set_inheritable(fd, True)` or `execv` closes the fd (lock appears to work but
  doesn't — waiter entered after 0.1 s instead of 2.1 s).
- Installed headers can be OLDER than dylib (`cannot find
  'bt_cerebro_configure_returns' in scope` while `nm` shows the export) — pick the
  modulemap include root by content digest, staged to `.iter72_lane_swift/include/<digest>`.
- Readiness probe must compile the WHOLE module (support + port + sibling TUs), else
  unresolved symbols cascade into false `typecheck_error`. Take the first `: error:` line.
- A giant single `+` print chain (19 lines/40 interpolations) times out Swift
  typecheck — use `var diag:[String]` + `append` + `joined()`.
- Port is a MULTI-FILE module: exactly one `@main` (harness declares none), and **no
  `-O`** — optimization changes results.
- `--output` is semantic: port walks upward to config/data — keep
  `<cell>/results/swift_result.json`.
- Multi-feed union clock folds secondary-feed-only stamps (`bar_num` 6130 vs 6135) —
  inject prev-close carry-forward into main feed inside the port.
- Do NOT derive calendar buckets from epoch — use loader-parsed Y/M
  (`(4*doe+3)/1461` has ~600 errors at century leap boundaries).
- Annualization constant: `24*60*252 = 362880` (once mistyped as 302400).
- TradeAnalyzer long/short buckets count at CLOSE, total counts at OPEN —
  `buy+sell == trade_num - open` (equals trade_num only when flat at end).

## Result JSON

`benchmarkWriteOutput(output, payload)` writes and prints. Fields: `engine, rows,
read_time_sec, run_time_sec, total_time_sec, bar_num, buy_count, sell_count,
win_count, loss_count, sum_profit, sharpe_ratio, annual_return, max_drawdown,
total_trades, return_rate, final_value`.

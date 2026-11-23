# Target: Go

Status: **real-implementation based** (back_trader benchmark `bb_adx_strategy` +
iter71/72 Go lane). Read `languages/_implementation-notes.md` first for the shared
binding routes, order-status numbers and result contract.

## Verified routing

- Route: **SWIG**, not C ABI. Facade import path is literally `bt "backtrader"`
  (`back_trader_swig_go.dylib` + generated `back_trader_swig.go`).
- Runner: `scripts/run_go_swig_strategy_backtests.py`.
- Benchmark sample: `benchmarks/strategies/bb_adx_strategy/languages/go/bb_adx_strategy.go` (4.3 KB, 127 lines).

## Real API mapping (from the sample, verbatim)

| backtrader | Go facade |
|---|---|
| `bt.Strategy` subclass | `struct { *bt.Strategy }`, ctor `bt.NewStrategy(strategy, name)` |
| `__init__` indicators | `Start()`: `bt.Indicators.ADX(strategy.Data, 14)`, `bt.Indicators.Bollinger(strategy.Data.Close, 20, 2)` |
| `next()` | `Next()` |
| `self.data.close[0]/[-1]` | `strategy.Data.Close.At(0) / .At(-1)`; `bb.Top/Mid/Bot.At(0/-1)` |
| NaN guard | `bt.IsFinite(...)` (go1.27 GOPATH has no `math.IsFinite`) |
| position | `strategy.Position().Size` |
| orders | `Buy(1)/Sell(1)/BuyStop(1,top)/SellStop(1,bot)/Close()` |
| `notify_order` | `NotifyOrder`, clears `orderPending` |
| Cerebro | `bt.NewCerebro(cash)`, `cerebro.Broker().SetCash`, `cerebro.AddData(&bt.GenericCSVData{...})`, `cerebro.RunResult(engine)` |
| output | `bt.NewBenchmarkOptions().WithEngine().WithBarNum(...).WithBuyCount(...)...`, `bt.WriteBenchmarkResult(output, engine, ...)` |

Data feed uses `bt.DataPath("bb_adx_strategy", "sh600000.csv")`, `FromDate/ToDate`,
`DateTimeFormat: "%Y/%m/%d"`, column indices `Open:4 High:2 Low:3 Close:1 Volume:5`,
`Headers:true`, `SortByDateTime:true`, `NumericFilters`.

## Build / run (real commands)

```bash
# one-time binding build (no network)
cmake --build <build-dir> --target backtrader_go_package
cmake --build <build-dir> --target backtrader_go_module
python3 scripts/iter71_go_prewarm_archive.py --build-dir <build-dir> --restore

python3 scripts/run_go_swig_strategy_backtests.py \
  --build-dir build_iter54_lang15_strict \
  --strategies-root strategies --strategy <cell> \
  --out-dir /tmp/go_run --prewarm-timeout 1800
# per cell: go run <source>.go --output <result> --engine go --config <cell>/config.yaml
```

Env: `BACK_TRADER_REPO_ROOT`, `GO111MODULE=off`,
`GOPATH=<build-dir>/go_lane_gopath`,
`CGO_LDFLAGS=<swig_dir>/back_trader_swig_go.{dylib,so} -Wl,-rpath,<swig_dir>`.

Result path: main tree `<cell>/go_result.json`, benchmark `results/go_result.json`.

## Go-specific pitfalls (verified)

- **cgo first-compile cost**: 15 MB `back_trader_swig.go` → ~28 MB C TU; a serial
  `cc1` took **6077 s** (≈100 min) cold. Preserve `go_lane_gopath/pkg/**/*.a` —
  losing it repays the cost. Never edit `.iter71_go_lane/go_stage/**`.
- `native.go` wants `libback_trader_swig_go.so` but the build emits no `lib` prefix;
  runner builds a symlink farm. Do not patch `native.go`.
- **Never `import "back_trader_swig"`** in a port — `backtrader/internal/swig` already
  contains the same binding; double link ⇒ `multiple definition of Swig_Director...`.
- Counts must come from TradeAnalyzer buckets via `ids.Run` + `TradeCounts.Options` +
  `WithBuyCount/...`. `GetByName("trades").GetAnalysis()` is broken in Go (integer
  counters read as kind `integer` → all 0); a second `cerebro.Run` also yields 0.
  Old `grep -c WithBuyCount` gate is obsolete.
- macOS fault `0x1`: stage `native.go` arity mismatch → 7-param dylib writes past
  registers; surviving view uses `Line(LineNames()[0])`. 36 of 98 default
  constructors lack `set_line_names` and silently return NaN (e.g. Momentum) — read
  such indicators via `Close.At(0)-Close.At(-N)` instead.
- Runner default `--strategies-root` scans benchmark tree and can report `total: 0`
  with rc=0; use a fresh `--out-dir` and confirm `status_counts.ran` equals cell count.
  `mkdir -p <cell>/results` before running.

## Result JSON

Written by `benchmark.go` `WriteBenchmarkResult()` — strict ordered serialization,
`never accepts native result JSON`; non-finite floats → `null`;
`max_drawdown = result.MaxDrawdown * scale` (benchmark scale 100). Fields:
`engine, bar_num, buy_count, sell_count, win_count, loss_count, sum_profit,
read_time_sec, run_time_sec, total_time_sec, sharpe_ratio, annual_return,
max_drawdown, total_trades, final_value, return_rate`.

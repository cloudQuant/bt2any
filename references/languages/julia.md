# Target: Julia

Status: **real-implementation based** (benchmark sample + iter72 Julia lane).
Read `languages/_implementation-notes.md` first.

## Two routes — pick one

| Route | How | Runner |
|---|---|---|
| **C ABI via Backtrader.jl** (main) | `using Backtrader`, package does `ccall((:bt_..., _LIB), ...)` | `run_julia_cabi_strategy_backtests.py` |
| Iter54 "C source→dylib" adapter | compile strategy's C file to `.build/lib<name>_julia_cabi_adapter.dylib`, `Libdl.dlopen`+`dlsym(:julia_cabi_main)` | `iter54_cabi_adapter.jl` (not runner-driven) |

Sample: `languages/julia/bb_adx_strategy.jl` (3.34 KB, 27 lines). Package:
`bindings/c/adapter/julia/package/Backtrader/src/Backtrader.jl` (107 KB, v0.59.0),
native lib at package-relative `deps/usr/lib/libback_trader_c_abi.{dylib,so,dll}`
(asserted in `__init__()`). Note: package `_LIB` is package-relative; the runner's
`BACK_TRADER_C_ABI_LIB` mainly serves the iter54 adapter route — do not mix.

## Real API mapping (verbatim)

| backtrader | Julia |
|---|---|
| strategy | `mutable struct X <: Strategy`; `Backtrader.start!(s)`, `Backtrader.next!(s)`, `Backtrader.notify_order!/notify_trade!` |
| indicators | `s.adx = indicators.ADX(c; period=14)`, `indicators.BollingerBands(c; period=20, devfactor=2.0)` |
| indicator value | `something(s.adx)[0] / [-1]` (fields are `Union{Nothing,IndicatorLine}`) |
| data | `data(c).close[0] / [-1]` |
| orders | `buy!(c,1)`, `sell!(c,1; price=top, exectype=3)`, `close!(c)` |
| status | `o.status in (1,2)` Submitted/Accepted, `==4` Completed |
| trades | `t.isclosed`, `t.pnlcomm` |
| feed | `PandasCSVData(data_path(...); name, fromdate, todate, filter_positive_close, sort_datetime)` |
| args | `args(v)` filters `"--"` elements, pairs into Dict |

`exectype=3`, status `1/2/4` are bare numeric literals — no symbolic constants.

## Build / run (real commands)

```bash
env BACK_TRADER_REPO_ROOT=<repo> BACKTRADER_DATA_DIR=<repo>/datas \
    BACK_TRADER_C_ABI_LIB=<cabi_lib> BACK_TRADER_C_ABI_BUILD_DIR=<cabi_dir> \
    DYLD_LIBRARY_PATH=<cabi_dir> LD_LIBRARY_PATH=<cabi_dir> \
  julia <source>.jl --output <cell>/results/julia_result.json --engine julia
```
Adapter compilation (macOS, iter54 route):
```bash
cc -std=c11 -D_DARWIN_C_SOURCE -Dmain=julia_cabi_main \
  -I<repo>/bindings/c/include -I<repo>/benchmarks/language_scripts/c \
  <strategy>.c -L<cabi_dir> -lback_trader_c_abi -dynamiclib \
  -Wl,-rpath,<cabi_dir> -o .build/lib<strategy>_julia_cabi_adapter.dylib
```
Julia 1.13.0, Backtrader.jl 0.59.0, `Libdl` stdlib.

## Julia-specific pitfalls (verified)

- Bare numeric order types/statuses — write by semantic value, not names.
- `something(s.indicator)` required to unwrap `Union{Nothing,...}`.
- **Result JSON is hand-written by regex extraction**: `number(j,k)=parse(Float64,
  match(Regex("\"$k\":([-0-9.eE]+)"), j).captures[1])`. Charset lacks `+` →
  scientific notation with `+` or missing key throws. `max_drawdown` is multiplied
  by 100 in the sample. `@sprintf("%.17g")` depends on C locale; non-finite sharpe
  has no null guard (regex misses it).
- `args(v)` filters all `"--"` tokens (Julia passes `--` through ARGS).
- `try/finally close(c)` — Cerebro must be explicitly closed or native handle leaks.
- Single-slot `pending` latch + `exectype=3` two-leg stop strategy; do not "fix".
- Batch worker SHA-256 checks manifest/worker/source/native; output uses `O_EXCL`;
  strategy name must match `^[A-Za-z0-9][A-Za-z0-9_.-]*$`.

## Result JSON

`main()` builds one `@sprintf` JSON string with fixed field order
`engine, rows, read_time_sec, run_time_sec, total_time_sec, bar_num, buy_count,
sell_count, win_count, loss_count, sum_profit, sharpe_ratio, annual_return,
max_drawdown, total_trades, return_rate, final_value, results_time_sec`;
`mkpath(dirname(out))`, `write(out, p*"\n")`, `println(p)`.

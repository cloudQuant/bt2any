# Target: R

Status: **real-implementation based** (benchmark sample + `.iter72_r_lane` handbooks).
Read `languages/_implementation-notes.md` first.

## Two routes coexist — pick one

| Route | Sample/runner | Notes |
|---|---|---|
| **SWIG R package** | `languages/r/bb_adx_strategy.R` (4.97 KB), `run_r_swig_strategy_backtests.py` | `require("backtrader")`, helpers from `back_trader_swig_facade.R` |
| **C ABI (iter71/72)** | `run_r_cabi_strategy_backtests.py`, `.iter72_r_lane/{bt_r_runtime.R,bt_r_pandas.R,bt_r_shim.c}` | base R + handwritten C bridge via `.Call` |

The benchmark sample is the **SWIG** form (uses `load_dated_ohlcv_csv`,
`write_strategy_result_json` from the R package facade). Iteration-72 real ports use
the **C ABI** form described below.

## Why a C bridge is required (verbatim rationale from `bt_r_shim.c`)

Base R (4.3.3, no jsonlite/Rcpp/FFI extension) can only call a C library via `.C`
or `.Call`. `.C` cannot call back into R, so per-bar strategy callbacks would have to
live in C — making the port a C port. `.Call` can `Rf_eval` R closures from C, so the
trading rules stay in `<name>.R`. Hence the handwritten shim.

Three shared files (pin to the cell, never edit):
- `bt_r_runtime.R` (67 KB, version "R2") — ~530 of ~670 lines of an accepted port;
  port keeps only params/indicator chain/next()/analyzer kwargs/cell gates.
  `bt_r_require("R2")` asserts the version. Loads shim via `dyn.load(Sys.getenv("BT_R_SHIM"))`,
  `getNativeSymbolInfo(..., PACKAGE="bt_r_shim")`. All numbers go through
  `bt_r_num(text)` → `.Call(r_parse_doubles, text)` using libc `strtod` (not R's
  `as.numeric`, which is not correctly rounding).
- `bt_r_pandas.R` (11.86 KB) — base-R pandas shim `btp_*`: fillna/shift/diff/pct_change/
  ffill/cumsum/rolling_*/ewm_mean/... calibrated to pandas 2.2.3 (1st-order rel≤1e-13,
  std/var rel≤1e-12). `rolling std/var ddof=1`, min_periods counts non-NaN,
  ewm `adjust=TRUE, ignore_na=FALSE`.
- `bt_r_shim.c` (61.91 KB) — trampoline re-entering R for start/next/notify_*;
  `R_registerRoutines(info, NULL, k_call_methods, NULL, NULL)`, `R_useDynamicSymbols(FALSE)`.

## Real API mapping (SWIG sample)

| backtrader | R facade |
|---|---|
| strategy class | R6-style object using `Strategy` from `backtrader` package |
| indicators | `self$set_indicator("adx", indicators$ADX(self$data, period=14L, ...))`, `indicators$BollingerBands(self$data$close, ...)` |
| data | `self$data$close[0L] / [-1L]`, `self$bbands$top[-1L]` |
| orders | `self$sell(data=self$data, size=1.0)`, `self$buy(..., price=top, exectype=Order$Stop)`, `self$close(data=self$data)` |
| order status | `Order$Submitted/Accepted/Completed`; `order$is_buy`, `trade$isclosed`, `trade$pnlcomm` |
| output | `write_strategy_result_json(output, engine, result, ..., max_drawdown_scale=100.0, win_count, loss_count, sum_profit)` |

`Order$Stop <- 3L` is hardcoded by the port — the facade does not expose Stop.

## Build / run (real commands)

SWIG:
```bash
cmake --build build_iter54_r_work --target install_backtrader_r_package
Rscript <source>.R --output <cell>/results/r_result.json --engine r
```
C ABI (shim compiled once, cached by sha256 of `bt_r_shim.c`[:16]):
```bash
PKG_CPPFLAGS=-I<repo>/bindings/c/include \
PKG_LIBS="-L<cabi_dir> -Wl,-rpath,<cabi_dir> -lback_trader_c_abi -lm" \
  R CMD SHLIB -o bt_r_shim.so bt_r_shim.c
# env: BT_R_SHIM=<shim.so>, TZ=UTC, BACK_TRADER_REPO_ROOT, LD_LIBRARY_PATH
Rscript --vanilla <port>.R --output <result> --engine r
```
C ABI path needs **no R package install**; only `R`, gcc/cc and the C ABI library.

## R-specific pitfalls (verified lane facts)

- `[0L]`=current, `[-1L]`=previous — R-native `[1]` is wrong.
- `Order$Stop <- 3L` must be added by port.
- `NaN > x` is `NA`, not `FALSE`: flags must be `!is.na(v) & v > t`.
- Float comparison uses EPS `1e-12` (`bb_adx_le/ge`).
- R text→double is not correctly rounded — use `r_parse_doubles` (strtod); `%.17g`
  can switch to scientific notation and make the engine read a different finite number.
- `bt_r_round()` uses `sprintf("%.Nf")` to emulate Python `round`; banker's rounding
  differs (2.675 → R 2.68 / Python 2.67) — affects lot size and money fields.
- Bar shift applied BEFORE closed `[from,todate]` filter with integer epoch seconds;
  15/1440 day is not representable — boundary 1 ulp drops a bar (bar_num off-by-one).
- `stop()` inside a callback longjmps across engine C++ frames → fatal; wrap every
  callback body in `tryCatch(..., error=...)`, shim pins SEXP with `R_PreserveObject`.
- Counts from TradeAnalyzer buckets, not `notify_trade` self-accumulation.
- `bt_cerebro_get_analyzer` cannot resolve implicitly registered analyzers — read
  values from `bt_cerebro_run_json` tree.
- **Single R process** at a time; max 3 real R runs per cell, third failure → hand back.
- Hard boundaries: write only `<cell>/languages/r/<name>.R`; pinned `bt_r_*.R`/
  `bt_r_shim.c` never edited; `run.py`/`config.yaml`/`py_result.json`/`datas/*.csv`
  read-only; never run any Python/C++ oracle.

## Result JSON

SWIG: `write_strategy_result_json()`. C ABI lane: runtime hand-writes with `sprintf`+
`writeLines`, `%.17g` round-trip, non-finite → `null`, fixed 11 contract fields +
`engine/rows/read_time_sec/run_time_sec`.

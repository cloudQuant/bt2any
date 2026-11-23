# Target: C

Status: **real-implementation based** (benchmark `bb_adx_strategy` + iter72 C lane).
Read `languages/_implementation-notes.md` first.

## Verified routing

- Route: **C ABI** (`libback_trader_c_abi.dylib/.so`) + header-only facade
  `backtrader_c_facade.h`. **Not SWIG.**
- Runner: `scripts/run_c_abi_strategy_backtests.py`; lane `scripts/iter72_lane_c.py`.
- Sample: `benchmarks/strategies/bb_adx_strategy/languages/c/bb_adx_strategy.c` (6.43 KB, 143 lines).

## Real API mapping (verbatim from sample)

```c
#include <backtrader_c_facade.h>
enum { BT_ORDER_STOP = 3 };
static void check_status(bt_status_t s) { if (s != BT_STATUS_OK) { fprintf(stderr,"%s\n", bt_last_error()); exit((int)s); } }
```
- lifecycle: `bt_strategy_callbacks_t callbacks = {0}; callbacks.start=...;
  callbacks.nextstart=bb_adx_next; callbacks.next=bb_adx_next;
  bt_strategy_create("BBADXStrategy", callbacks, NULL);`
- engine metric config in `start()`: `bt_strategy_enable_engine_metrics`,
  `bt_strategy_set_engine_metric_profit_mode(BT_ENGINE_METRIC_PROFIT_PNLCOMM)`,
  `..._trade_classification_mode(BT_ENGINE_METRIC_TRADE_CLASSIFY_PNLCOMM)`,
  `..._zero_pnl_policy(BT_ENGINE_METRIC_ZERO_PNL_LOSS)`,
  `..._order_count_mode(BT_ENGINE_METRIC_ORDER_COUNT_COMPLETED)`.
- indicators: `bt_strategy_add_adx(strategy,"adx",14)`,
  `bt_strategy_add_bollinger(strategy,"bb","close",20,2.0)`.
- data: `bt_strategy_data_line(strategy,0,"close",0/-1)`,
  `bt_strategy_indicator_value(strategy,"adx")`,
  `bt_strategy_indicator_line_value(strategy,"bb","top"/"mid"/"bot",-1/0)`;
  `isfinite` on all values.
- orders: `bt_strategy_sell_order_data(..., top, BT_ORDER_STOP, &note)`,
  `bt_strategy_buy_order_data(...)`, `bt_strategy_close_order_data(...)`.
- data feed: `bt_package_resolve_data_path(...)` → `bt_pandas_data_feed_create_from_csv_ex(...)`,
  `bt_broker_setcash`, `bt_cerebro_add_pandas_data`, `bt_cerebro_add_standard_analyzers`.

## Build / run (real command)

```bash
cc -std=c11 -D_DARWIN_C_SOURCE \
  -I <repo>/bindings/c/include -I <repo>/bindings/c/package/include \
  -I <repo>/benchmarks/language_scripts/c \
  <source>.c -L <build>/bindings/c -lback_trader_c_abi \
  -Wl,-rpath,<build>/bindings/c -lm -o <exe>
<exe> --output <cell>/results/c_result.json --engine c
```
`-lm` needed for `nearbyint/fmod/floor/exp` in header-only facade. env:
`BACK_TRADER_REPO_ROOT`, `DYLD_LIBRARY_PATH`/`LD_LIBRARY_PATH` to `cabi_dir`,
`TZ=UTC` (iter72 lane). No Cargo/SWIG/third-party modules.

## C-specific pitfalls (agent-brief + lane records, verified)

- `--output` is used to **infer the strategy dir** (read config/data) — must be
  `<cell>/results/c_result.json`; `/tmp` gives `cannot read data file: /datas/...`.
  iter72 writes in-tree then `cp` to evidence dir under `fcntl.flock` (no `flock(1)`
  on macOS). `mkdir -p <evidence>/_bin` before first cold run.
- `bt_cerebro_get_analyzer(...,"tradeanalyzer")` returns NULL — read counts from
  `bt_cerebro_run_json` → `analyzers.by_name` with a depth-1 scoped walker (a naive
  walk is polluted by per-bar `total_value`). Open-trade count key is
  `analyzers.by_name.tradeanalyzer.total.open` (scalar), not `open.total`.
- `CommissionType` is **Fixed=1 / Percentage=0** (opposite of Python 0/1);
  one-arg `bt_broker_setcommission` and four-arg futures-percent are different
  families — wrong one gives correct counts, wrong money. `setcommission_full`
  automargin `NaN` = Python default.
- Latch: `bt_strategy_order_target_percent_order(...,&note)` with `note.ref != 0`;
  free run JSON with `bt_string_free`. There is **no** `bt_strategy_data_open/high/low`
  — use `bt_strategy_standard_data_line_value(s,i,line,ago)`.
- Two ago conventions: `bt_strategy_indicator_line_value` uses NEGATIVE ago
  (`-1` = previous), `bt_strategy_data_line(...,0)` has `ago=0` as current; mixing
  shifts the indicator chain one bar.
- Order status table: `Created0 Submitted1 Accepted2 Partial3 Completed4 Canceled5
  Expired6 Margin7 Rejected8` (from `include/order.h`); facade name table can be
  misaligned — verify before branching on status.
- `datetime` line is Rata Die day serial: minute bars offset `62135683200.0 s`,
  **daily bars `62135769599.999992 s`** — clock gates must be cell-calibrated.
- No `bt_strategy_trade_isopen`, only `isclosed`; the latter returns bool as int and
  returns 0 on error — reversing the condition is completely silent.
- `nextstart` falls back to `next`, `prenext` does not — attaching only `next`
  already excludes warm-up; an extra manual gate drops `minperiod-1` bars.
- Folded ports include `bt_cabi_harness.c` + a generated `#pragma weak bt_h_*` block;
  iter71 compiles only `<cell>.c`, iter72 compiles **all** `.c` in dir — mismatch
  gives "proxy self-check green, ledger rejected_not_run".
- stdout prints only payload; no probe keys in result JSON. Missing result file ≠ not
  run (runner unlinks each round) — use summary `ran`.

## Result JSON

Engine serialization; port only writes: `bt_cerebro_run_benchmark_json(cerebro,
engine, read_time, &payload)` → `bt_package_write_json(output_path, payload)` →
`puts(payload)` → `bt_string_free(payload)`. Port writes no field itself. Fields:
`engine, rows, read_time_sec, run_time_sec, total_time_sec, bar_num, buy_count,
sell_count, win_count, loss_count, sum_profit, sharpe_ratio, annual_return,
max_drawdown, total_trades, final_value, return_rate, results_time_sec`.

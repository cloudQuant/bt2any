# Target: Lua

Status: **real-implementation based** (benchmark sample + `.iter72_lane_lua/brief.py`).
Read `languages/_implementation-notes.md` first.

## Verified routing — no LuaJIT/ffi

- Lua 5.5 (PUC-Rio) here has **no FFI library and no LuaJIT**. Do not write
  `local ffi = require("ffi")`.
- Main route: **C ABI** via a hand-written C host embedding liblua and exporting
  `libback_trader_c_abi` `bt_*` to a Lua facade (`iter71_cabi_backtrader.lua`).
  Runner `run_lua_cabi_strategy_backtests.py`, host
  `benchmarks/language_scripts/lua/backtrader_cabi_host.c` (46.8 KB).
- SWIG route also exists (`run_lua_swig_strategy_backtests.py`, `back_trader_swig.so`).
- Sample: `languages/lua/bb_adx_strategy.lua` (4.25 KB) — package-consumer form
  `local bt = require("backtrader")`, `bt.Strategy:extend()`.

## Real API mapping (sample)

| backtrader | Lua facade |
|---|---|
| strategy | `bt.Strategy:extend()`, `init()`, `next()` |
| indicators | `bt.indicators.ADX(self.data.close,{period=14})`, `bt.indicators.BBands(...)` |
| data | `self.data.close[0] / [-1]`, `self.adx[0]` |
| orders | `self:sell({size=1})`, `self:buy({size=1, price=top, exectype=bt.Order.Stop})`, `self.closepos` |
| feed | `bt.feeds.CSVData({dataname, numeric_filters={{column="close",op=">",value=0}}})` |
| run | `cerebro:run(engine)`, `strategies[1].result` |
| output | `string.format` JSON → `io.open(output,"w")` + `print(payload)` |

## Build / run (real commands)

```bash
python3 scripts/run_lua_cabi_strategy_backtests.py \
  --build-dir build_iter54_lang15_strict --strategies-root strategies/<cat> \
  --strategy <dir> --out-dir /tmp/lua_run --timeout 300
# host compiled by runner:
# cc -O2 -std=c11 -I$HOME/.local/include/lua-5.5 -I<repo>/bindings/c/include \
#    -o artifacts/iter71_lua/host/backtrader_lua_host \
#    benchmarks/language_scripts/lua/backtrader_cabi_host.c \
#    -L$HOME/.local/lib -llua -L<build>/bindings/c -lback_trader_c_abi -lm \
#    -Wl,-rpath,$HOME/.local/lib -Wl,-rpath,<build>/bindings/c
```
Env overrides: `BACK_TRADER_LUA_INCLUDE`, `BACK_TRADER_LUA_LIBDIR`, `BACK_TRADER_LUA_LINK`.
`--rebuild-host` forces recompile. SWIG route requires `LUA_PATH`/`LUA_CPATH` and
**removes** `DYLD_LIBRARY_PATH`/`LD_LIBRARY_PATH` to avoid loading R's same-named module.

## Lua-specific pitfalls (brief.py HARD_FACTS)

1. Only stdlib `math/string/table/io/os.time` + `iter71_cabi_backtrader` — no third-party require.
2. Result JSON whitelist: 11 contract fields + `engine/rows/read_time_sec/run_time_sec`;
   one extra key ⇒ `result_invalid` even if all values right. `null != 0`; bool illegal; counts integers.
3. Counts from TradeAnalyzer buckets, not self-count. `total.open` exists only when
   opened>closed — flat book `to_int` aborts.
4. Engine clock is **float serial in DAYS**; M15 advances `15/1440`, D1 publishes at
   `day+1-1ulp`; `t == prev+1` is always wrong.
5. `error()` inside a callback makes host `_exit(4)` with NO result file — diagnostics
   outside callbacks.
6. `value(1)` reads the FUTURE bar; warm-up uses `0/-ago`.
7. Only `nil/false` are false in Lua; `0.0` and `nan` are truthy — flags need `==0`/`~=0`.
8. `a and nil or b` is not a ternary; non-finite witnesses → JSON null before encoding.
9. `notify_trade` gets only `(strategy, trade_id)` — entry price must come from
   `notify_order`'s `order.executed.price`.
10. `setminperiod` does not control dispatch — registering indicators does; unregistered
    minperiod=1, so Python warm-up must be implemented in the port itself.
11. Two percent-commission shapes must not mix (`broker_add_futures_percent_commission`
    keeps `mult`, `broker_setcommission_full` does not).
12. `order_target_percent`: only `bt_strategy_order_target_percent_order` returns an order handle.
13. `Submitted` and `Accepted` both notify for one ref — `acks == submissions` is not invariant.
14. `timeframe` is a numeric `bt_timeframe_t` (Minutes=4, Days=5); resampledata takes
    source feed handle, derived feed index=1.

## Result JSON

Sample `string.format("%.17g/%d")` hand-built JSON: `engine, bar_num, buy_count,
sell_count, win_count, loss_count, sum_profit, read_time_sec, run_time_sec,
total_time_sec, sharpe_ratio, annual_return, max_drawdown, total_trades,
return_rate, final_value, results_time_sec, rows`. C ABI runner writes `<cell>/lua_result.json`,
SWIG writes `results/lua_result.json`.

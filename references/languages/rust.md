# Target: Rust

Status: **real-implementation based** (back_trader benchmark `bb_adx_strategy` +
`.iter72_rust_lane/PORTER.md`). Read `languages/_implementation-notes.md` first.

## Verified routing

- Route: **C ABI** (`libback_trader_c_abi`) via Rust facade crate `backtrader` +
  fixture crate `iter60_fixture_support`. **Not Cargo default, not SWIG.**
- Runner: `scripts/run_rust_c_abi_strategy_backtests.py`; lane orchestrator
  `scripts/iter72_lane_rust.py` (prewarm rlib cache).
- Sample: `benchmarks/strategies/bb_adx_strategy/languages/rust/bb_adx_strategy.rs` (11.47 KB, 319 lines).

## Real API mapping (from the sample)

| backtrader | Rust facade |
|---|---|
| strategy class | `struct` + `impl Strategy for ...` (initialize/nextstart/next/notify_order/notify_trade) |
| indicators | `backtrader::indicators::adx/bollinger` + `core.label_indicator("adx"/"bb", &handle)` |
| data | `core.data().line("close").get(0/-1)` wrapped in `check_status(...)` |
| indicator line | `check_status(check_status(core.indicator_handle("bb")).line(core,"top")).get(-1)` |
| orders | `core.submit_buy/sell(OrderRequest{data,size,price,execution_type:MARKET/STOP,...})`, `core.submit_close(CloseRequest{...})` |
| Cerebro | `Cerebro::new(cash)`, `feeds::pandas_csv(path,name,from,to,...)`, `cerebro.add_strategy_factory(...)`, `add_analyzers(&AnalyzerCollection::standard())` |
| output | `run_and_publish(&mut cerebro, &args, read_time)` → frozen engine report |

`use iter60_fixture_support::{configure_metrics, count_bar, count_buy, ...,
ProfitMode::PnlComm, ZeroPnlPolicy::Loss, OrderCountMode::Completed}` – configure
these to match the oracle's counting semantics.

## Build / run (real commands)

```bash
python3 scripts/iter72_lane_rust.py --prewarm    # builds rlib warm cache (fcntl lock + rename)
# compiles:
#   rustc --crate-name=backtrader --crate-type=rlib <facade> -o .iter72_rust_lane/rlib/libbacktrader.rlib
#   rustc --crate-name=iter72_lane --crate-type=rlib <support> --extern backtrader=... -o .../libiter72_lane.rlib
rustc --edition=2021 <port>.rs \
  --extern backtrader=.../libbacktrader.rlib --extern iter72_lane=.../libiter72_lane.rlib \
  -L dependency=.../rlib -L native=<cabi_dir> -l dylib=back_trader_c_abi \
  -C link-arg=-Wl,-rpath,<cabi_dir> -A warnings -o <exe>
<exe> --output <cell>/results/rust_result.json --engine rust
```
Env: `BACK_TRADER_REPO_ROOT`, `DYLD_LIBRARY_PATH`/`LD_LIBRARY_PATH` prefixed with
`cabi_dir`. Existing rlibs: `libbacktrader.rlib` 8.78 MB, `libiter72_lane.rlib` 1.17 MB.

## Rust-specific pitfalls (PORTER.md, verified)

- **No Linux Cargo route**: `build.rs` panics `"ships no native ABI asset for
  linux-x86_64"`. Use rustc rlib cache, not `cargo build`.
- Worker shell's `rustc` is NOT on PATH — use `$HOME/.cargo/bin/rustc`. Toolchain
  rustc 1.98.1; `f64::ulp()` does not exist (E0599).
- `get(ctx, ago)` ago equals Python `line[ago]`: previous bar is `-1`; positive is
  look-ahead. Sample ports only use `.get(0)`/`value()`.
- **tann is not bindable**: compute `annual_return=(ravg*tann).exp_m1()` yourself;
  daily 252, M15 `24*60*252=362880` — read from each cell's run.py.
  `SharpeConfig::new` defaults `annualize:false, risk_free_rate:0.01` — set explicitly.
- `percabs` entry-dependent: `CommInfoBase.percabs` default false, `COMM_PERC and not
  percabs` divides commission by 100; passing `true` for a custom subclass makes fees
  100× and adds MARGIN rejects. `setcommission_full` automargin `f64::NAN` = Python default.
- Feed missing `<DATE>,<TIME>` ⇒ engine **silently dispatches 0 bars** (run "succeeds",
  analyzers empty). Fixed column order `datetime,time,open,high,low,close,volume,openinterest`.
- `self.position` truth = `size != 0`; `self.close()` does not immediately change size.
- `E0601 no main` often means truncated port — run `rustc --emit=metadata` first.
  Diagnostics go to `cell_run.log`, never into payload.
- `--config` is inferred from `--cell` path (`port.parents[2]/config.yaml`); keep temp
  copies inside the cell's `languages/rust/`.
- `notify_order` timing skew: fork delivers new bar then `_brokernotify()` then
  `strat._next()`; reading `exec_data` in callback sees an unconsumed bar → reversal
  entries shift one bar.
- `Vec<f64>` PartialEq says NaN≠NaN — use NaN-aware `same_line()` for line parity gates.

## Result JSON

Engine-native frozen report (`run_capture(..., FrozenReport)` → `capture.summary_json()`
→ `publish_payload()`), not hand-written. `canonical_nonfinite_json()` rewrites
`NaN/Infinity` to `{"kind":"float","value":"nan"/"inf"/"-inf"}`. Fields include
`engine, rows, read_time_sec, run_time_sec, total_time_sec, bar_num, buy_count,
sell_count, win_count, loss_count, sum_profit, sharpe_ratio, annual_return,
max_drawdown, total_trades, return_rate, final_value, results_time_sec`.

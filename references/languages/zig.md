# Target: Zig

Status: **real-implementation based** (benchmark sample + `会话14-zig技能提案.md`).
Read `languages/_implementation-notes.md` first.

## Verified routing — NOT `@cImport` in the port

- Port imports a typed package: `const bt = @import("backtrader")`.
  `@cImport` exists only INSIDE the package
  (`bindings/c/adapter/zig/package/backtrader/src/backtrader.zig:3-7`), which also
  `@embedFile`s the macOS dylib and dlopens it on other platforms.
- Iter72 port is a **library shape** (no `main`): exports
  `pub fn run(allocator, config) !bt.Iter67Result`. Runner
  `scripts/run_iter72_zig_cell.py` (+ `scripts/iter72_zig_build.py` content-addressed
  sandbox). **Legacy `run_zig_strategy_backtests.py` is NOT applicable** (flat-compile
  for benchmark form).
- Sample: `languages/zig/bb_adx_strategy.zig` (7.2 KB), package 2057 lines.
- Zig ≥ 0.16.0.

## Real API mapping (sample)

| backtrader | Zig |
|---|---|
| strategy | `struct`, `pub fn start(state:*@This(), ctx:*bt.StrategyContext)!void`, `next` |
| indicators | `bt.indicators.ADX(ctx,.{.name="adx",.period=14})`, `bt.indicators.Bollinger(ctx, ctx.data().close, .{...})` |
| data | `ctx.data().close.at(0) / at(-1)` |
| position | `ctx.position().size` |
| orders | `ctx.sell(1.0)`, `ctx.buyStop(1.0, top)`, `ctx.sellStop(1.0, bot)`, `ctx.close()` |
| status | numeric `1/2/4` hardcoded |
| lifecycle | `pub const lifecycle: bt.StrategyLifecycle = .{ .start=.start, .nextstart=.next, .next=.next, .notify_order=true, .notify_trade=true };` |

## Build / run (real commands)

Iter72 main line:
```bash
zig build -Doptimize=ReleaseFast --cache-dir <HARNESS>/.zig-cache --prefix <out_prefix>
# cwd = content-addressed compile root; port copied byte-for-byte as src/strategy_impl.zig + hash check
<exe> --config <evidence>/config.json --output <evidence>/zig_result.json --nonce <32+ hex>
```
Legacy (reference only): `zig build-exe <port>.zig iter54_c_support_exports.c
-O ReleaseFast -I bindings/c/include -L <cabi_dir> -lback_trader_c_abi -lc -femit-bin=<exe>`.
Env `BACK_TRADER_C_ABI_PATH`; `build.zig.zon` uses relative path to backtrader package.
Trusted launcher accepts ONLY `--config/--output/--nonce` (NO `--engine`), nonce ≥32 chars.

## Zig-specific pitfalls (verified)

- **`--abi` default trap**: launcher default points at a STALE core
  (`build/bindings/c/...`, mtime 2026-09-01). Omitting it silently swaps core →
  `run_failed` + `MissingNativeSymbol` that looks like a port bug. Lane now exits
  on missing. Cross-run ABI identity must be in the fingerprint.
- `toOwnedSlice` clears the list and struct literal fields evaluate left-to-right:
  `return .{ .bars = try bars.toOwnedSlice(a), .count = bars.items.len };` gives count
  **always 0** → `NoSourceRows`, `ran=0` with empty `mismatched_fields`. Bind length first.
- `@max(@as(c_int,1), x)` returns `u31` in Zig 0.16 (`-a` then fails) — write
  `fn atLeastOne(x: c_int) c_int`.
- `zig build` MUST use `-Doptimize=ReleaseFast` or linking fails
  `undefined symbol: bt_last_error`.
- **needle contract**: build scans whole lines for `XxxField(config,name)` shapes —
  comments containing such shapes create fake needles; `trimField(...) else "0"`
  creates needle `0`. Fix comments/helper names, not the gate.
- runner face: sandbox config `file` is a BARE filename (`input.csv`), cwd is sandbox;
  splitting dirname → `MalformedFeedPath`, `ran=0`. Accepted port shape `orelse "."`.
- Multi-symbol feed keys `<symbol.lower()>_file` (e.g. `dxyn_file`); non-OHLC inputs
  via `overrides["keys"]` absolute paths.
- Shared cache keyed by absolute build root — compiling in per-run evidence dir
  re-emits all compile units; `build_slot` serializes.
- Result JSON hand-built via `std.fmt.allocPrint` with `jsonNumber(raw,key)` simple
  `indexOf` extraction (no `+` handling), `max_drawdown * 100`, written via
  `std.Io.Dir.cwd().createFile`. Receipt records toolchain/ABI hash/input fingerprint/11-field diff.

## Result JSON

Fields: `engine, rows, read_time_sec, run_time_sec, total_time_sec, bar_num,
buy_count, sell_count, win_count, loss_count, sum_profit, sharpe_ratio,
annual_return, max_drawdown, total_trades, return_rate, final_value,
results_time_sec`. Runner writes `<evidence>/zig_result.json`. Note `cpp_result.json`
sits at cell root, not under `cpp/`.

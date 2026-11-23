# Target: Ruby

Status: **real-implementation based** (benchmark sample + `.iter72_rb_lane` prompts).
Read `languages/_implementation-notes.md` first.

## Verified routing

- C ABI route: ruby stdlib **Fiddle** (1.1.1) — no gem/bundler/package install.
  Port dlopens `libback_trader_c_abi.so`; `BACK_TRADER_C_ABI_PATH` overrides.
  Runner `run_ruby_cabi_strategy_backtests.py`.
- SWIG route: `ruby -I <build>/bindings/swig <source> ...`, `back_trader_swig.rb/.bundle`.
- Sample `languages/ruby/bb_adx_strategy.rb` (5.21 KB) is the SWIG package form
  (`require "backtrader"`, default engine `ruby_swig_package`).

## Real API mapping (sample)

| backtrader | Ruby facade |
|---|---|
| strategy | `class X < Backtrader::Strategy` |
| indicators | `Backtrader.indicators.AverageDirectionalMovementIndex(data, period: 14)`, `BollingerBands(data, period:..., devfactor:...)` |
| data | `resolve_data_path`, `Feeds::GenericCSVData.new(dataname:..., sort_by_datetime:true)` + `add_numeric_filter("close",">",0.0)` |
| orders | `buy/sell/close` wrappers; backtrader indexing `[0]`/`[-1]` |
| run | `cerebro.run(engine: args["--engine"]).first` |
| output | `numeric(v)` maps NaN/Inf→nil, `JSON.generate(payload)` → `File.write(--output)` + puts |

## Build / run (real commands)

```bash
python3 scripts/run_ruby_cabi_strategy_backtests.py \
  --build-dir build_iter54_lang15_strict --strategies-root strategies/<cat> \
  --strategy <dir> --out-dir /tmp/ruby_run --timeout 300
python3 scripts/run_ruby_swig_strategy_backtests.py \
  --build-dir build_iter54_ruby_current --strategies-root benchmarks/strategies \
  --strategy bb_adx_strategy --out-dir artifacts/iter54_ruby/run
```
C ABI deps: ruby + stdlib `fiddle/json/fileutils/tmpdir` + built `libback_trader_c_abi.so`.
Runner creates `results/` (missing dir was a false `missing_output`). Result
`strategies/<dir>/results/ruby_result.json`.

## Ruby-specific pitfalls (harness + lane, verified)

- **Fiddle cannot call `bt_strategy_create`**: `bt_strategy_callbacks_t` is 88 bytes
  passed BY VALUE → libffi fills only scalars, RIP=0x7. Use
  `bt_strategy_create_callbacks` (eight bare function pointers + user_data).
- Closures are `Fiddle::Closure::BlockCaller`; every closure and malloc'd buffer must
  be parked in `@keep_alive` or GC frees the ffi_closure → next dispatch segfaults.
- Raising inside a callback cannot unwind libffi — process aborts (exit 3).
- `JSON.generate` RAISES on NaN/Infinity — every payload value passes a finiteness
  gate → JSON null. `Float#to_s` may emit exponent form; `BtCabi.float_repr` expands
  digit by digit (engine CSV can't read exponent). `Integer('08')` raises (octal) —
  use `Integer(t,10)`.
- Indicator/data `ago` IS the bare backtrader subscript (`0==[0]`, `-1==[-1]`).
- `bt_broker_getcash` returns pointer bit patterns (shared defect) — take EVERY money
  number from engine run JSON, do not compute yourself.
- Mandatory skeleton: `cp .iter72_rb_lane/harness/bt_cabi_harness.rb <cell>/languages/ruby/`,
  sha256 prefix `905aa9c021a531d0`; main file only cell logic with
  `require_relative 'bt_cabi_harness'`. Before attempts run `lint_return.py`,
  `lint_analyzers.py`, `lint_percabs.py` — all must report `findings: 0`.
- `H.analyzers` with `returns:{tann:52}` (no timeframe) raises `undefined method
  'to_sym' for nil` — supply `{timeframe: :days, compression: 1, tann: 52}`.
- `BtCabi.shift` only supports `k>0`; `shift(-1)` raises — use `arr[i+1]`.
- Ruby negative indexes wrap — sliding window `values[i-w]` must check `negative?`.
- Commission: `setcommission(...)` one-arg ⇒ `H.broker(style: :simple)`;
  `addcommissioninfo(SomeCommInfo(...))` ⇒ `percabs: 0` (reference already divided by
  100). `add_futures_percent_commission(commission, MULT, MARGIN, name)` argument order
  is OPPOSITE of Python `ComminfoFuturesPercent(commission, margin, mult)`.
- `sum` must be explicitly left-associative (not `Array#sum`, which is compensated).
- prep-resample family: derived frame as sole feed must not also feed base frame;
  `bar_num == derived trimmed rows`, `P = rows - bar_num + 1 == 1`; bin labels are
  right boundaries; 8h `closed='right'` membership is `(epoch-1)/8h`.
- `if` direction must be copied line by line (a reversed `unless ... == 'lot'` once
  made counts correct and 5 money fields wrong).
- Engine time is not unix epoch — do not assert equality on engine dt.

## Result JSON

`FileUtils.mkdir_p(File.dirname(--output))`, `File.write(..., "#{JSON.generate(payload)}\n")`,
`puts JSON.generate(payload)`. `numeric()` guarantees NaN/Inf → JSON null.

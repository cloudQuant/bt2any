# Target: Perl

Status: **real-implementation based** (benchmark sample + `.iter72_perl_lane` briefs).
Read `languages/_implementation-notes.md` first.

## Verified routing — SWIG only, no FFI

- `iter72_lane_perl.py:10-28`: perl 5.38.2 / SWIG 4.5.1; "lane is a SWIG lane, not
  an FFI lane. `FFI::Platypus`, `FFI::C`, `Inline::C` and every other CPAN FFI module
  are absent." **Do not write FFI::Platypus code.**
- Sample: `languages/perl/bb_adx_strategy.pl` (7.33 KB), `use Backtrader`,
  `use Backtrader::Benchmark`, package-only Iter66 facade.
- Runner: `scripts/run_perl_swig_strategy_backtests.py` (there is no Perl C ABI lane).

## Real API mapping (sample)

| backtrader | Perl facade |
|---|---|
| strategy | package with `Backtrader` facade, `$core->register_indicator(...)` |
| indicators | `$state->{adx} = Backtrader::ADX->new(); $adx->set_period(14)` |
| data | `$data->configure_generic_csv(Backtrader::Benchmark::nan(), ",", "%Y/%m/%d", 0, "%H:%M:%S", 1,0,-1, 4,2,3,1,5,-1)` |
| orders | `$core->sell_order_data(0, 1.0)`, `$core->buy_order_data(0,1.0,$topNow,$Backtrader::Order::Stop)` |
| run | `$cerebro->run_json($engine)` |
| output | `Backtrader::Benchmark::write_benchmark_json($output,$engine,$result,...,$options)` with `with_max_drawdown_scale(100.0)` |

Native: `<build>/bindings/swig/perl/auto/back_trader_swig/back_trader_swig.<dlext>` + staged
facade `<build>/bindings/swig/perl_package/Backtrader/lib`.

## Build / run (real commands)

```bash
python3 scripts/run_perl_swig_strategy_backtests.py \
  --build-dir build_iter54_perl_current --strategies-root benchmarks/strategies \
  --strategy bb_adx_strategy --out-dir artifacts/iter54_perl/run
# per cell: perl <source> --output <result> --engine perl
```
Env: `PERL5LIB` prefixed with swig dir and `benchmarks/language_scripts/perl`;
**remove** `DYLD_LIBRARY_PATH`/`LD_LIBRARY_PATH` or R's same-named module loads first.
Windows/Strawberry: `STRAWBERRY=/c/Strawberry`, `LC_ALL=C LANG=C`, unset
`PERL5LIB/PERL_MM_OPT/PERL_MB_OPT` in `perl_env.sh`; Strawberry's gcc must match the
built runtime. No CPAN installs. Result `strategies/<dir>/results/perl_result.json`.

## Perl-specific pitfalls (PORT_AUTHORING_BRIEF.md, verified)

1. Git Bash `/usr/bin/perl` and mingw64 toolchain must not take PATH — compiler picks
   wrong runtime. Strawberry has no `C.UTF-8`; msys locale warns/crashes → `LC_ALL=C LANG=C`.
2. Line reads are **signed**: `value(ago)`/`data_line(...,ago)` positive = FUTURE,
   previous bar is `-1`.
3. `Position` SWIG proxy only via `swig_price_get()`/`swig_size_get()`;
   `$position->{price}` is undef and silently zeroes equity (~12k drift observed).
4. Out-of-range negative index on staged signal column wraps to column end — no naive
   length gate.
5. Multi-feed lane entry only `compression: 1`; `resampledata` must build from raw leg —
   putting resample interval into source feed sends wrong bar count (383 H4 vs 400).
6. Slow-leg custom indicators dispatch on **clock ticks**, not every signal bar
   (400 slots produced 3614 `next()` calls).
7. `bt.ind.SumN` uses `math.fsum`; naive window sum drifts ~5e-15 and can flip decisions.
8. This fork's `buy_bracket/sell_bracket` default to `Order.Limit` + `price=None`,
   filling at decision bar close — do not change to Market. Bracket orders armed in
   `notify_order` receive clones and never fire — arm in `notify_trade` or use refaddr.
9. Coarse leg delivered at declaration stamp, not `stamp+compression` — the donor
   "+" note is wrong.
10. `!ref($v)` rejects `JSON::PP::Boolean` (silently zeroes config bools); `gmtime`
    0-based month makes H6 stamp one month early.
11. `configure_analyzers` dies on unresolved input — use `override` to express oracle.
12. `run_perl_swig_strategy_backtests.py` is Iter54 benchmark runner and cannot drive
    the main tree.

## Result JSON

`write_benchmark_json($output,$engine,$result,$read,$run,$total,$options)` with
`with_max_drawdown_scale(100.0)`. Fields mirror the benchmark 16-key set
(`engine/rows/bar_num/.../total_trades/final_value/return_rate/...`).

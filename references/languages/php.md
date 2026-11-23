# Target: PHP

Status: **real-implementation based** (benchmark sample + `.iter72_php_lane/BRIEF.md`).
Read `languages/_implementation-notes.md` first.

## Verified routing

- Main C ABI route: PHP 8.3 bundled **FFI extension** `FFI::cdef` — no build step,
  no install. Port self-declares a subset of `back_trader_c.h` and dlopens
  `libback_trader_c_abi.so`. Runner `run_php_cabi_strategy_backtests.py`.
- SWIG route: `back_trader_swig_php.so` extension, `run_php_swig_strategy_backtests.py`.
- Sample `languages/php/bb_adx_strategy.php` (7.49 KB) is a **Composer package consumer**
  (`require_once __DIR__.'/vendor/autoload.php'`, `use Backtrader\{...}`) — this is NOT
  the lane's single-file FFI form. Lane ports must not `require` the SWIG `Backtrader.php`.

## Real API mapping (sample + lane)

| backtrader | PHP facade / FFI |
|---|---|
| strategy | class extends `Backtrader\Strategy` (composer) or `require 'bt_cabi_harness.php'` (lane) |
| indicators | `Indicators::ADX($this->data, period: 14)`, `Indicators::BollingerBands(...)`, `Order::Stop` |
| data | `$this->data` lines via facade; FFI: `indicator_line_value(id,line,-1)` NEGATIVE ago |
| orders | `$this->sell()`, `$this->buy(exectype: Order::Stop, price: $stop)` |
| feed | `Feeds::GenericCSVData(dataname: ..., dtformat:'%Y/%m/%d', datetime:0, ..., close:1, ...)->addNumericFilter('close','>',0.0)` |
| run | `$cerebro->run($args['--engine'])`, `$strategies = ...` |
| output | `json_encode($payload, JSON_UNESCAPED_SLASHES | JSON_THROW_ON_ERROR).PHP_EOL` → `file_put_contents(--output)`, echo |

## Build / run (real commands)

```bash
python3 scripts/run_php_cabi_strategy_backtests.py \
  --build-dir build_iter54_lang15_strict --strategies-root strategies/<cat> \
  --strategy <dir> --out-dir /tmp/php_run --timeout 300
# lane env: BACK_TRADER_C_ABI_PATH=<cabi lib>, BACK_TRADER_REPO_ROOT,
#           LD_LIBRARY_PATH/DYLD_LIBRARY_PATH to cabi dir
python3 scripts/run_php_swig_strategy_backtests.py \
  --build-dir build_iter54_lang15 --strategies-root benchmarks/strategies \
  --strategy bb_adx_strategy --out-dir artifacts/iter54_php/run
# SWIG: php -d extension=<build>/bindings/swig/back_trader_swig_php.so <source> ...
```
Requirement: `extension_loaded("ffi") == ok`. Lane forbids apt/pecl/composer/pip/npm installs.
Result `strategies/<dir>/results/php_result.json`.

## PHP-specific pitfalls (BRIEF.md, verified)

1. Pinned core is `build/bindings/c/libback_trader_c_abi.dylib` (sha256 `88ef3ad...`) — **never rebuild**; old `build_iter54_lang15_strict/*.so` is a previous-host path.
2. Port is self-contained single file with inline `FFI::cdef` declaring only the symbols
   the cell uses; do NOT use SWIG `Backtrader.php` facade.
3. Repo root from `dirname(__DIR__,5)`, cell from `dirname(__DIR__,2)` — do NOT infer
   strategy dir from `--output`.
4. `FFI::cdef` does not parse the whole `back_trader_c.h`: `extern "C" {` and doc
   comments are rejected — transcribe the needed subset.
5. `bt_strategy_callbacks_t` CData must stay referenced (`$G->callbacks`).
6. `const char*` callback args arrive as PHP STRING (not CData); throwing from a
   callback is a hard fatal — collect status into `$G->abiErrors`, assert after.
7. Line reads are NEGATIVE ago: `indicator_line_value(id,line,-1)` = previous bar;
   positive reads future.
8. Duplicate declarations/typedefs in `FFI::cdef()` fatal at construction — use
   `harness/base_cdef_full.txt` and scaffold `--harness`.
9. Reference formula by spelling: `bt.indicators.SMA` ⇒ exact sum/fsum; hand-written
   loop ⇒ left-associative. Switching causes divergence.
10. Dependency registry only counts real `require/include/use`; 35 on-disk ports used 0 SWIG facades.

## Result JSON

`json_encode($payload, JSON_UNESCAPED_SLASHES | JSON_THROW_ON_ERROR).PHP_EOL`,
mkdir then `file_put_contents(--output)`, `echo`. Fields mirror Node's set with
`$args['--engine']` echoed verbatim.

# Target: C#

Status: **real-implementation based** (benchmark sample + iter71 C# lane).
Read `languages/_implementation-notes.md` first.

## Verified routing

- Main route: **C ABI + hand-written P/Invoke facade** (`Backtrader.cs`,
  `private const string Library = "back_trader_c_abi"`, `[DllImport(Library,
  CallingConvention=Cdecl)]`). Runner `run_csharp_cabi_strategy_backtests.py`.
- Old SWIG route (`run_csharp_strategy_backtests.py`, Iter54 proxies) **cannot compile
  Iter71 ports** — do not use it for new ports.
- Sample: `languages/csharp/bb_adx_strategy.cs` (7.13 KB, 30 compressed lines).

## Real API mapping (verbatim)

| backtrader | C# facade |
|---|---|
| strategy | `class X : Strategy`, override `Start(StrategyContext)`, `Next(StrategyContext)` |
| indicators | `_adx = Indicators.ADX(context,"adx",14)`, `Indicators.BollingerBands(context,"bb",20,2.0)`, `_top = Indicators.Line(context,"bb","top")` |
| data | `context.Data.Close[0] / [-1]`, `_top[0] / [-1]` |
| NaN guard | `AllFinite(...)` using `double.IsFinite` |
| position | `context.Position.Size` |
| orders | `context.Sell(1.0)`, `context.Buy(new OrderRequest{Size=1, ExecutionType=ExecutionType.Stop, Price=top})`, `context.Close()` |
| order status | `OrderStatus.Submitted=1 / Accepted=2 / Completed=4` |
| trades | `NotifyTrade` reads `trade.IsClosed`, `trade.PnlComm` |
| data path | `DataPath(name)` checks `BACKTRADER_DATA_DIR`, `BACK_TRADER_DATA_DIR`, `BACK_TRADER_REPO_ROOT/datas|tests_python/datas|root` |

`ExecutionType.Stop = 3`. `context.Close()` uses a native "all-position sentinel"
(Size defaults `double.NaN`).

## Build / run (real commands)

Runner generates `<out>/_proj/<strategy>/Lane.csproj` that compiles **port.cs +
facade Backtrader.cs into one assembly** (facade's P/Invoke class is assembly-internal):
```xml
<OutputType>Exe</OutputType><TargetFramework>{tfm}</TargetFramework>
<Nullable>enable</Nullable><ImplicitUsings>enable</ImplicitUsings>
<AllowUnsafeBlocks>true</AllowUnsafeBlocks><EnableDefaultCompileItems>false</EnableDefaultCompileItems>
<Compile Include="port.cs"/><Compile Include="Backtrader.cs"/>
```
```bash
dotnet build <out>/_proj/<s>/Lane.csproj -c Release -o <exe_dir> --nologo
dotnet <exe_dir>/lane_<s>.dll --output <cell>/results/csharp_result.json --engine csharp
```
TFM inferred from `dotnet --version` major (fallback net10.0). Env `DOTNET_CLI_TELEMETRY_OPTOUT=1`,
`DOTNET_NOLOGO=1`, `LD_LIBRARY_PATH`/`DYLD_LIBRARY_PATH` to native lib dir (the
`DllImport` has no resolver hook). No NuGet packages — JSON via `System.Text.Json`.

## C#-specific pitfalls (verified)

- **Must launch `dotnet <dll>`**, not the apphost executable — dotnet lives under
  `~/.local` so the apphost cannot find the runtime.
- Export library path before run; `DllImport("back_trader_c_abi")` has no resolver.
- Do not hardcode TFM; `Nullable=enable` + `EnableDefaultCompileItems=false` means
  both port and facade must be explicit `<Compile Include>`.
- Single `_order` latch: `Next()` returns while `_order is not null`;
  `NotifyOrder` returns on Submitted/Accepted and clears only on terminal states.
- `max_drawdown` taken directly from analyzer `NestedNumber(drawdown,"max","drawdown")`
  — **no ×100** (R/Julia do ×100; all converge to 0.0376801 in benchmark JSON).
- `FiniteOrNull` maps non-finite Sharpe to `null`; `AllFinite` filters warm-up NaN.
- Old SWIG lane used different field names (`bar_num→bar_count`,
  `win_count→winning_trades`, `total_trades→trade_count`) — do not mix.

## Result JSON

`WriteResult()` builds `Dictionary<string,object?>`, `JsonSerializer.Serialize`,
`File.WriteAllText(output, json + newline)`, echoes to console. Fields:
`engine, rows, bar_num, buy_count, sell_count, win_count, loss_count, sum_profit,
read_time_sec, run_time_sec, total_time_sec, sharpe_ratio, annual_return,
max_drawdown, total_trades, final_value, return_rate, results_time_sec`.

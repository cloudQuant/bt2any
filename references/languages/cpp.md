# Target: C++

Status: detailed mapping. Requires a target framework — either a native C++ backtester
you provide, or `back_trader_cpp` (C++20 static core). This skill does not ship the core.

## Framework options

1. **back_trader_cpp** — native C++ port of backtrader semantics (Strategy/Cerebro/
   Broker/DataFeed/Indicator/Analyzer). Provide its root via `config.yaml` →
   `target_framework.cpp.root`; link `back_trader::cpp_core` + Threads.
2. **Custom/native C++ engine** — if the user has one, map backtrader concepts to it
   and keep the same 11-field result JSON.

## Concept mapping (backtrader → C++)

| backtrader | back_trader_cpp |
|---|---|
| `bt.Strategy` | subclass `back_trader::strategy::Strategy` |
| `__init__` build indicators | `start()` override, `add_indicator(...)`, `indicator->start()` |
| `next()` | `void next() override` |
| `notify_order(order)` | `void notify_order(shared_ptr<OrderBase>) override` |
| `notify_trade(trade)` | `void notify_trade(string_view trade_id) override` |
| `self.data.close[0]` | `current_close(primary_data_raw())` |
| `self.data.<extra>[0/1]` | `data(0)->getline("<name>")->current()/at(1)` |
| `bt.indicators.BollingerBands` | `indicators::bollinger::BollingerBands` (lines: mid/top/bot) |
| `bt.indicators.SMA(line, period)` | `MovingAverageSimple(data_vec, period, "<line_name>")` |
| `self.buy(size=...)` / `sell` / `close` | `buy(nullptr, size)` / `sell` / `close(data)` |
| `cerebro.addanalyzer(Returns/Sharpe/...)` | `cerebro.addanalyzer<Returns>()` etc. |
| `ComminfoFundingRate` | `comminfo::ComminfoFundingRate(CommInfoConfig{...})` |

## Build / run

```bash
cmake -S <dir> -B <dir>/build -DCMAKE_BUILD_TYPE=Release \
  -DBACK_TRADER_ROOT=<path/to/back_trader>
cmake --build <dir>/build -j4
<dir>/build/<strategy> --config <dir>/config.yaml
```

Emit `results/cpp_result.json` with the 11 fields. If using back_trader, take counts
from TradeAnalyzer analyzer output, not from strategy-side counters.

## C++-specific pitfalls

- C++ standard must be C++20 for back_trader_cpp.
- `CommInfoConfig`: set `percabs=true` to match backtrader's decimal-fraction
  commission; set `stocklike=true` if the oracle includes position market value in
  equity. Mismatch here distorts final_value and max_drawdown.
- Custom columns (funding/mark price) must be registered as extra data lines; an
  OHLCV-only feed drops the signal silently.
- Many CSV datasets use `M/D/YYYY H:MM`. CsvDataFrame's auto parser typically
  requires a 4-digit year first; parse explicitly with `strptime("%m/%d/%Y %H:%M")`.
- Default compiler warnings about `Sharing is only supported...` on macOS are benign.

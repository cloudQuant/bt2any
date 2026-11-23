# Target: Java

Status: detailed mapping. Requires a target framework — either a Java backtest engine
you provide, or a Spring-based strategy service (e.g. bitrue-strategy-service) whose
Runner you can drive from a test/CLI. This skill does not ship the engine.

## Framework options

1. **Service Runner风格**（如 bitrue-strategy-service）：策略实现为 `XxxStrategyRunner`
   + `XxxRuntimeState`，由工厂装配 client/adapter；可执行入口通常是测试目录里带
   `@Test` 的工具类。优点：贴近生产；缺点：强依赖 Spring/RPC/DB glue。
2. **轻量 Java 回测引擎**（若用户提供）：把 backtrader 概念映射到该引擎的
   Strategy/Broker/Data/Indicator API，输出同样 11 字段 JSON。

## Concept mapping (backtrader → Java service runner)

| backtrader | Java (service style) |
|---|---|
| `params` | `XxxParams` POJO，由 `StrategyParamsCodec.parseXxx` 解析 |
| `__init__` indicators | `tryInit()` 中构造/计算指标（如 `TechnicalIndicatorCalculator.calcBollingerBands`） |
| `next()` | tick/bar 主循环（Runner 的 `onBar`/`tick`） |
| `self.position.size` | `PositionInfo` / `getPosition()` |
| `notify_order` | order adapter 回调 / `orderGateway.findByClientId` |
| `buy/sell/close` | `MarketOrderHelper.placeOpenOrder` / close 订单 |
| `ComminfoFundingRate` | 回测 client 的 `settleFunding()`（正费率多头付） |
| analyzers | 回测结果对象（ROI/MDD/winRate/tradeNum） |

## Build / run（服务风格示例）

```bash
export JAVA_HOME=$(brew --prefix openjdk@17)/libexec/openjdk.jdk/Contents/Home
cd <service-root>
mvn -q -pl <app-module> -am -Dtest=<EntryTest> -Dsurefire.failIfNoSpecifiedTests=false test
# 产物（若测试导出）搬到 strategies/<...>/results/java_result.json
```

**JDK**: many such services require Java 17; default newer JDKs break Lombok. Use the
project's `.java-version` / toolchain.

## Java-specific pitfalls

- Enum additions are ordinal-sensitive (`ordinal+1` code mapping) — append only.
- New param types need registration in multiple places (subtype annotations, codec,
  factory switches, i18n keys). Missing one causes runtime deserialization failure.
- Funding settlement lives in the backtest client, not the Runner — when extracting
  a pure kernel, move that rule with the strategy.
- Counts from trade/analyzer results, not from counters in the bar loop.
- BigDecimal precision: match scale/rounding of the oracle (e.g. 8-digit funding MA).
- Avoid hardcoding absolute CSV paths in the port; read from config.yaml.

---
name: bt2any
description: >
  Convert a Python backtrader strategy into an equivalent strategy in any target
  language (C++, Java, Go, Rust, R, C, C#, Julia, Lua, Node.js, Perl, PHP, Ruby,
  Swift, Zig), with metric parity against the Python result. Use for converting,
  porting, rewriting, validating, debugging, or handing off backtrader strategy
  conversions. One strategy at a time, parity-first, no Python/pybind fallback in
  the target port. Works across agents (CodeBuddy, Claude Code, Codex, Kiro).
---

# bt2any — Backtrader Python → Any Language

## Role

You are an expert quantitative-strategy porting engineer. You convert ONE Python
`backtrader` strategy into ONE target language with **exact metric parity** against
the original Python run. You know both the source semantics (order lifecycle,
broker simulation, indicators, analyzers, data feeds, timers) and the target
language's backtesting framework.

You never guess an API signature. You verify every mapping against the language
profile in `references/languages/<lang>.md`, the semantic notes, and the bundled
examples. When uncertain, read a reference before writing code.

## Hard constraints (non-negotiable)

1. **One strategy at a time.** No batch conversion. Full context + validation per strategy.
2. **Never modify the source Python strategy.** Treat it as the oracle.
3. **Metric parity is the contract.** The target result JSON must match `py_result.json`
   field-by-field within `abs<=1e-6` OR `rel<=1e-6`.
4. **Counts come from the framework's TradeAnalyzer**, never self-incrementing
   counters in `next()`. `null` is not `0` — if the oracle says null, emit null.
5. **No value-level backfill.** Never edit a result JSON to "make it match". Fix the
   port, rebuild, rerun. Do not fabricate metrics.
6. **Framework APIs over hand-rolled equivalents.** Use the target framework's
   indicators / broker / analyzers. A custom indicator must be a real subclass.
7. **Use the effective parameter names** from the source (`riskfreerate`, not
   `risk_free_rate`; `percabs`, not `percent_abs`). Mark ambiguities explicitly.
8. **Derive semantics from THIS strategy's Python source and config**, not from a
   template. Analyzer settings, minperiod, feed columns and commission must be
   read per strategy.
9. **Static "matched" or a checked box is not acceptance** — the target must really
   run, produce a result JSON, and pass the validator.
10. **Stop after 3 failed attempts** on the same cell; record evidence and blocker,
    do not lower the tolerance.

## Capability boundary — read this first

This skill produces a **semantic port + output contract + validation scaffold**.
Whether the generated port is directly runnable depends on the target framework:

- **Self-contained frameworks** (e.g. a target-language backtester you already have,
  or `back_trader`'s C ABI facade): the skill can generate a runnable port that
  programs against that framework's API.
- **No target framework available**: the skill generates a compilable skeleton with
  clearly marked TODOs at the framework boundary, the full strategy logic, and a
  validator. It must not claim the port is validated until a real run passes.

If a target framework is required but unavailable, say so explicitly and ask the
user for its path/install. Do not silently substitute a Python/pybind shim.

## Input / Output contract

**Input**: one Python file containing a `bt.Strategy` subclass plus a runner that
builds `Cerebro`, feeds, broker, analyzers, and emits a `py_result.json`-style
metric dict.

**Output** (under `<strategy_dir>/`, one target language at a time):

```
<strategy_dir>/
  config.yaml                 # cash / commission / params / data paths (single source of truth)
  run.py                      # original Python runner (unchanged, oracle)
  py_result.json              # baseline produced by running run.py
  languages/<lang>/<strategy>.<ext>   # target-language port
  results/<lang>_result.json  # target metrics, same 11-field schema
  context.md                  # compressed analysis of the Python strategy (generated)
  analysis.json               # machine-readable source facts (generated)
```

**The 11-field result schema** (all languages, exactly these keys):

```
bar_num, buy_count, sell_count, win_count, loss_count, trade_num,
final_value, sharpe_ratio, annual_return, max_drawdown, return_rate
```

Allowed extra keys (benchmark/perf only):
`engine, rows, read_time_sec, run_time_sec, total_time_sec, process_wall_time_sec,
results_time_sec, strategy_function_time_sec, sum_profit`.
Alias: `total_trades` → `trade_num`. Any other extra key is `rejected_field_error`.

## Workflow (6 gates)

1. **Baseline** — run the original Python runner, save `py_result.json`. Never edit it.
2. **Context** — generate `context.md` + `analysis.json` from the Python AST
   (`scripts/analyze_source.py`). Load only the references and 1–3 examples you need.
3. **Implementation** — read the target profile (`references/languages/<lang>.md`),
   write the port using framework APIs, keep config in `config.yaml`.
4. **Parity** — build/run the target, emit `results/<lang>_result.json`, validate with
   `scripts/validate_result.py py_result.json results/<lang>_result.json`.
5. **Regression** — re-run both sides from a clean state; confirm deterministic parity.
6. **Knowledge** — if you discovered a new mapping/pitfall, append it to the
   appropriate `references/languages/<lang>.md` with a short evidence note.

Do not advance past a gate until it passes.

## Context budget (load only what you need)

| File | Load when |
|---|---|
| `SKILL.md` (this file) | Always |
| `references/conversion-contract.md` | Before any conversion (result schema, tolerances, null semantics) |
| `references/semantic-patterns.md` | When the strategy uses orders, indicators, multi-timeframe, resample, feature cache, timers |
| `references/validation.md` | When parity fails — symptom index + repair playbook |
| `references/layout.md` | When deciding output files/dirs |
| `references/languages/_implementation-notes.md` | Before any port — real-implementation facts (routes, order numbers, JSON, warm-up) |
| `references/languages/<lang>.md` | When implementing that language |
| `examples/*.md` | Pick 1–3 via the matrix below |

## Example selection matrix

| Strategy feature | Example |
|---|---|
| First conversion / simple buy-sell-close | `examples/simple_order_close.md` |
| Indicators and line slicing | `examples/indicators_and_lines.md` |
| Order lifecycle / stop / limit / OCO | `examples/order_lifecycle.md` |
| Commission / margin / futures | `examples/commission_and_margin.md` |
| Multi-timeframe / resample / replay | `examples/multi_timeframe.md` |
| Analyzers parity | `examples/analyzer_parity.md` |
| Dynamic sizing / target percent | `examples/dynamic_sizing.md` |
| Feature cache / external model | `examples/feature_cache.md` |
| Debug a mismatch | `examples/debug_with_tradelogger.md` |

## 16 target languages

`cpp`, `java`, `go`, `rust`, `r`, `c`, `csharp`, `julia`, `lua`, `node`, `perl`,
`php`, `ruby`, `swift`, `zig`, `python_swig`.

Each has `references/languages/<lang>.md` covering: target framework options,
API mapping from backtrader concepts, project layout, build/run commands, result
JSON emission, and language-specific pitfalls. Start with the profile before
writing code. If a profile is thin, say so and treat the port as a scaffold.

## Multi-agent usage

This repository keeps ONE canonical skill (`SKILL.md` at the root). Install it into
your agent with the installer, which creates/updates the agent's skill directory:

```bash
python3 scripts/install.py --agent auto     # detect from cwd / common dirs
python3 scripts/install.py --agent claude   # .claude/skills/bt2any
python3 scripts/install.py --agent codex    # .agents/skills/bt2any
python3 scripts/install.py --agent codebuddy# .codebuddy/skills/bt2any
python3 scripts/install.py --agent kiro     # .kiro/skills/bt2any
python3 scripts/install.py --agent all --target /path/to/project
```

The installer copies the whole skill (SKILL.md + references/ + scripts/ + examples/)
into the chosen directory. Re-run it to update. Frontmatter uses only `name` and
`description` for maximum compatibility across agents.

## Common mistakes

- Hardcoding cash/commission/params in target code instead of reading `config.yaml`.
- Building indicators in `__init__`/constructor instead of the framework's start hook.
- Guarding pending orders incorrectly → duplicate or skipped trades.
- Using different analyzer parameters (period / riskfreerate / annualization).
- Counting trades yourself instead of from TradeAnalyzer buckets.
- Treating `null` as `0`, or emitting extra keys in the result JSON.
- Widening the tolerance to force a pass.
- Assuming a language profile is complete when it is a scaffold — verify by running.

## Output standard

When you finish, report concisely:
- target language + framework used (and its path/version)
- files produced
- commands used for build and run
- parity result (field-by-field, max abs/rel diff)
- any unresolved gaps (with evidence), and whether the port is `validated`,
  `runs-but-mismatched`, or `scaffold-only`

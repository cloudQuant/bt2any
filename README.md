<div align="center">

# bt2any

**Convert Python `backtrader` strategies into 16 languages with metric parity**

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://www.apache.org/licenses/LICENSE-2.0)
[![Agents](https://img.shields.io/badge/Agents-CodeBuddy%20%7C%20Claude%20Code%20%7C%20Codex%20%7C%20Kiro-green.svg)](#install)

**English** | [**中文**](#-中文文档)

</div>

---

Convert a **Python `backtrader` strategy** into an equivalent strategy in **16 target
languages**, with metric parity against the Python result.

This repository is an **agent Skill**: one canonical `SKILL.md` plus references,
scripts, and examples. It works across CodeBuddy, Claude Code, OpenAI Codex, and Kiro
via the included installer.

> [!IMPORTANT]
> **This skill is built on top of the `back_trader` project and cannot succeed without
> it.** Every language profile documents a port that links
> `back_trader`'s native C ABI (`libback_trader_c_abi`) or its SWIG/pybind bindings,
> uses its `Cerebro` / `Broker` / `Strategy` / indicators / analyzers, and is built/run
> with its harness and runner scripts. bt2any itself ships **only** the conversion
> methodology, contracts, source-analysis scripts and a parity validator — **no
> backtest runtime, no engine, no language bindings**. Without a working `back_trader`
> checkout (core + bindings + runners) available, the skill can only produce a
> `scaffold-only` port; it cannot compile, run, or prove parity. See
> [Requirements](#requirements-back_trader-is-mandatory) and
> [What it does NOT provide](#what-it-does-not-provide) below.

## 16 target languages

`cpp` · `java` · `go` · `rust` · `r` · `c` · `csharp` · `julia` · `lua` · `node` ·
`perl` · `php` · `ruby` · `swift` · `zig` · `python_swig`

## What this skill provides

| Layer | Included |
|---|---|
| Methodology | one-strategy-at-a-time, 6 parity gates, evidence discipline |
| Contracts | 11-field result JSON, 1e-6 tolerance, null≠0, allowed extra keys |
| Source analysis | `scripts/analyze_source.py` (AST → `context.md` + `analysis.json`) |
| Validation | `scripts/validate_result.py` (language-independent JSON parity check) |
| Language profiles | `references/languages/<lang>.md` for all 16 targets, grounded in real `back_trader` ports (verified routing/API/build/pitfalls) + a shared `_implementation-notes.md` |
| Few-shot examples | 9 examples covering orders, indicators, analyzers, debugging |
| Multi-agent install | `scripts/install.py` → `.claude/`, `.agents/`, `.codebuddy/`, `.kiro/` |

## Requirements: `back_trader` is mandatory

bt2any is **not** a standalone translator. A successful conversion requires all of the
following to be present and working:

- A `back_trader` checkout with the **core** (`back_trader_cpp`) and its build artifacts:
  - C ABI shared library `build/bindings/c/libback_trader_c_abi.{dylib,so}`
  - (for SWIG targets) generated bindings under `build/bindings/swig/<lang>/`
  - facade packages/adapters per language (`bindings/c/adapter/<lang>/`,
    `bindings/swig/adapter/<lang>/`)
- The `back_trader` **runner scripts** (`scripts/run_<lang>_*_backtests.py`) and lane
  harnesses that the language profiles reference.
- The Python oracle strategy plus its 13-column backtest CSV, produced by
  `back_trader` / `backtrader` conventions.

Point the skill at your checkout via `config.yaml` →
`target_framework.<lang>.root` (or the matching `BACK_TRADER_*` environment variables
used by the runners). Set it once; profiles document the exact paths per language.

**If any of the above is missing, the conversion cannot be validated.** The skill will
mark the port `scaffold-only`, and no metric parity claim is valid.

## What it does NOT provide

- **No backtest runtime, engine, or bindings** — those all come from `back_trader`.
- No Python → target compiler. Conversion is AI-led, one strategy at a time, against
  the real back_trader API surface documented in the language profiles.
- No parity proof without a real run: `validate_result.py` only compares JSON that must
  come from actually executing the port through `back_trader`.

If `back_trader` is unavailable, the skill still produces a scaffold with the full
strategy logic and validation hook, but it explicitly reports `scaffold-only` — it
never claims parity without a real run.

## Install

Install into a project (auto-detects the agent, default Claude Code):

```bash
python3 scripts/install.py --agent auto --target /path/to/project
python3 scripts/install.py --agent codebuddy --target /path/to/project
python3 scripts/install.py --agent all --target /path/to/project
```

Install globally for the current user:

```bash
python3 scripts/install.py --agent claude --global
```

The installer copies `SKILL.md`, `references/`, `scripts/`, `examples/`, `agents/` into
`<target>/.<agent>/skills/bt2any/`. Re-run to update. Frontmatter uses only `name` and
`description` for maximum compatibility.

## Typical workflow

```bash
# 1. Analyze the source strategy
python3 scripts/analyze_source.py path/to/strategy.py --out-dir strategy_dir

# 2. (agent) run original strategy -> py_result.json; read context + language profile; write port

# 3. Build/run target -> results/<lang>_result.json

# 4. Validate parity
python3 scripts/validate_result.py strategy_dir/py_result.json \
  strategy_dir/results/cpp_result.json
```

## Repository layout

```
bt2any/
  SKILL.md                       # canonical skill (single source of truth)
  agents/openai.yaml             # Codex metadata
  references/
    conversion-contract.md       # 11 fields, tolerances, null semantics
    semantic-patterns.md         # backtrader behavior notes (language-agnostic)
    validation.md                # symptom index + repair playbook
    layout.md                    # output file conventions
    languages/                   # 16 language profiles
  examples/                      # 9 few-shot examples
  scripts/
    analyze_source.py            # Python AST -> context
    validate_result.py           # parity checker
    install.py                   # multi-agent installer
```

## Origin

Extracted from the `bt2cpp` skill in the `back_trader` project and generalized from a
C++-only converter into a multi-language conversion skill. The original bt2cpp skill
and back_trader repository remain untouched.

## License

Apache-2.0

---

# 📖 中文文档

[**English**](#bt2any) | **中文**

---

将 **Python `backtrader` 策略**转换为 **16 种目标语言**的等价策略，并以 Python 运行结果为基准做**指标对齐（metric parity）**。

本仓库是一个 **Agent Skill**：一份权威的 `SKILL.md`，加上参考文档、脚本和示例。通过内置安装器，可用于 CodeBuddy、Claude Code、OpenAI Codex 和 Kiro 等多种 Agent。

> [!IMPORTANT]
> **本 Skill 建立在 `back_trader` 项目之上，没有它就无法成功。** 每一份语言 profile 记录的移植版本都要链接 `back_trader` 的原生 C ABI（`libback_trader_c_abi`）或 SWIG/pybind 绑定，使用它的 `Cerebro` / `Broker` / `Strategy` / 指标 / 分析器，并依靠它的 harness 和 runner 脚本构建运行。bt2any 本身**只提供**转换方法论、产物契约、源码分析脚本和指标校验器——**不含回测运行时、引擎或语言绑定**。如果没有可用的 `back_trader` checkout（core + bindings + runners），本 Skill 只能产出 `scaffold-only`（仅骨架）的移植版本，无法编译、运行或证明对齐。参见下文的[运行环境要求](#运行环境要求必须依赖-back_trader)与[本 Skill 不提供什么](#本-skill-不提供什么)。

## 16 种目标语言

`cpp` · `java` · `go` · `rust` · `r` · `c` · `csharp` · `julia` · `lua` · `node` ·
`perl` · `php` · `ruby` · `swift` · `zig` · `python_swig`

## 本 Skill 提供什么

| 层面 | 内容 |
|---|---|
| 方法论 | 一次只转一个策略、6 道对齐关卡、证据纪律 |
| 契约 | 11 字段结果 JSON、1e-6 容差、null≠0、额外键白名单 |
| 源码分析 | `scripts/analyze_source.py`（AST → `context.md` + `analysis.json`） |
| 校验 | `scripts/validate_result.py`（语言无关的 JSON 对齐检查） |
| 语言 profile | 全部 16 种目标的 `references/languages/<lang>.md`，基于真实 `back_trader` 端口实现（经核实的路由/API/构建/坑），另有共享的 `_implementation-notes.md` |
| Few-shot 示例 | 9 个示例，覆盖订单、指标、分析器、调试 |
| 多 Agent 安装 | `scripts/install.py` → `.claude/`、`.agents/`、`.codebuddy/`、`.kiro/` |

## 运行环境要求：必须依赖 `back_trader`

bt2any **不是**独立的翻译器。一次成功的转换，要求以下各项齐备且可用：

- 一个 `back_trader` checkout，包含**核心**（`back_trader_cpp`）及其构建产物：
  - C ABI 共享库 `build/bindings/c/libback_trader_c_abi.{dylib,so}`
  - （SWIG 目标）`build/bindings/swig/<lang>/` 下生成的绑定
  - 各语言的 facade / adapter（`bindings/c/adapter/<lang>/`、`bindings/swig/adapter/<lang>/`）
- `back_trader` 的 **runner 脚本**（`scripts/run_<lang>_*_backtests.py`）以及各语言 profile 引用的 lane harness。
- Python 基准策略，以及按 `back_trader` / `backtrader` 约定产出的 13 列回测 CSV。

通过 `config.yaml` → `target_framework.<lang>.root`（或 runner 使用的相应 `BACK_TRADER_*` 环境变量）把 Skill 指向你的 checkout。配置一次即可；各 profile 会写明每种语言的精确路径。

**缺少上述任何一项，转换都无法被验证。** Skill 会把该移植版本标记为 `scaffold-only`，任何指标对齐声明都无效。

## 本 Skill 不提供什么

- **不提供回测运行时、引擎或绑定**——这些全部来自 `back_trader`。
- 不是 Python → 目标语言的编译器。转换由 AI 主导、一次一个策略，针对语言 profile 中记载的真实 `back_trader` API 进行。
- 没有真实运行就没有对齐证明：`validate_result.py` 只比较 JSON，而这些 JSON 必须来自通过 `back_trader` 真实执行该移植版本。

如果没有 `back_trader`，Skill 仍可产出包含完整策略逻辑和校验钩子的骨架，但会明确报告 `scaffold-only`——绝不在没有真实运行的情况下声称已对齐。

## 安装

安装到某个项目（自动检测 Agent，默认 Claude Code）：

```bash
python3 scripts/install.py --agent auto --target /path/to/project
python3 scripts/install.py --agent codebuddy --target /path/to/project
python3 scripts/install.py --agent all --target /path/to/project
```

为当前用户全局安装：

```bash
python3 scripts/install.py --agent claude --global
```

安装器会把 `SKILL.md`、`references/`、`scripts/`、`examples/`、`agents/` 复制到 `<target>/.<agent>/skills/bt2any/`。重新运行即可更新。frontmatter 只用 `name` 和 `description`，以获得最大兼容性。

## 典型工作流

```bash
# 1. 分析源策略
python3 scripts/analyze_source.py path/to/strategy.py --out-dir strategy_dir

# 2. （Agent）运行原策略 -> py_result.json；阅读 context 和语言 profile；编写移植版本

# 3. 构建/运行目标版本 -> results/<lang>_result.json

# 4. 校验对齐
python3 scripts/validate_result.py strategy_dir/py_result.json \
  strategy_dir/results/cpp_result.json
```

## 仓库结构

```
bt2any/
  SKILL.md                       # 权威 Skill（单一真源）
  agents/openai.yaml             # Codex 元数据
  references/
    conversion-contract.md       # 11 字段、容差、null 语义
    semantic-patterns.md         # backtrader 行为要点（语言无关）
    validation.md                # 症状索引 + 修复手册
    layout.md                    # 产物文件约定
    languages/                   # 16 种语言 profile
  examples/                      # 9 个 few-shot 示例
  scripts/
    analyze_source.py            # Python AST -> context
    validate_result.py           # 对齐校验器
    install.py                   # 多 Agent 安装器
```

## 来源

从 `back_trader` 项目的 `bt2cpp` Skill 提炼并泛化而来：由仅支持 C++ 的转换器扩展为多语言转换 Skill。原始的 bt2cpp Skill 与 back_trader 仓库均未改动。

## 许可证

Apache-2.0

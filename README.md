# bt2any

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

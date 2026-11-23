# bt2any

Convert a **Python `backtrader` strategy** into an equivalent strategy in **16 target
languages**, with metric parity against the Python result.

This repository is an **agent Skill**: one canonical `SKILL.md` plus references,
scripts, and examples. It works across CodeBuddy, Claude Code, OpenAI Codex, and Kiro
via the included installer.

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

## What it does NOT provide

A target-language backtest runtime. Generated ports program against the framework you
supply (e.g. `back_trader` C++ core, a Java strategy service, or a native backtester).
If no framework is available, the skill produces a **scaffold-only** port with the full
strategy logic and validation hook, and says so explicitly — it never claims parity
without a real run.

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

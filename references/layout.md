# Strategy Layout

One strategy per directory. One target language per conversion pass.

```
strategies/<category>/<NNNN_strategy_name>/
  config.yaml                       # cash, commission, mult, margin, params, data, analyzers
  run.py                            # original Python runner (oracle, never edited)
  strategy_<name>.py                # original Python strategy (oracle)
  py_result.json                    # baseline metrics from run.py
  context.md                        # generated compressed analysis
  analysis.json                     # generated machine-readable facts
  languages/<lang>/<name>.<ext>     # target-language port
  languages/<lang>/README.md        # framework/path/build notes for this port (optional)
  results/<lang>_result.json        # target metrics (11-field contract)
```

Language file extensions:

| lang | ext | lang | ext | lang | ext |
|---|---|---|---|---|---|
| cpp | .cpp | java | .java | go | .go |
| rust | .rs | r | .R | c | .c |
| csharp | .cs | julia | .jl | lua | .lua |
| node | .js | perl | .pl | php | .php |
| ruby | .rb | swift | .swift | zig | .zig |
| python_swig | .py | | | | |

## config.yaml rules

- All money/param values live here; target code reads them at startup.
- Date strings and data paths are relative to the config file's directory unless
  absolute paths are explicitly required by the target framework.
- Add a `target_framework` section when a port needs an external framework path:

```yaml
target_framework:
  cpp: { root: /path/to/back_trader, core_lib: /path/to/libcore.a }
  java: { root: /path/to/strategy-service, maven_module: bitrue-strategy-app }
```

## File naming rule

Target source filename = strategy directory basename + language extension.
Example: `0002_bollinger_funding` → `languages/cpp/0002_bollinger_funding.cpp`.
This keeps multi-language outputs aligned when diffed side by side.

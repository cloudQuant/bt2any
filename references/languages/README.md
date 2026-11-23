# Language Profiles

16 targets. Start with the shared [`_implementation-notes.md`](_implementation-notes.md) —
it contains facts extracted from real multi-language ports (binding routes, order
status numbers, the 11-field JSON in real files, warm-up semantics, evidence rules).

Every profile below is grounded in an actual strategy implementation in `back_trader`
(benchmark `bb_adx_strategy` with 15 language directories + iteration-71/72 lane
handbooks), not a generic template. They record the verified routing (C ABI vs SWIG),
real API mapping, actual build/run commands, runtime dependencies, and language-specific
pitfalls from the lane records.

| Language | Profile | Route (verified) | Key fact |
|---|---|---|---|
| C++ | [cpp.md](cpp.md) | back_trader C++ core | `BollingerBands`/`ComminfoFundingRate` native |
| Java | [java.md](java.md) | service Runner / custom engine | JDK 17, enum/subtype/codec wiring |
| Go | [go.md](go.md) | SWIG | cgo cold ~6077 s; counts from TradeAnalyzer buckets |
| Rust | [rust.md](rust.md) | C ABI + rlib cache | no Linux Cargo; `ago=-1` is previous bar |
| R | [r.md](r.md) | SWIG + C ABI shim | base R needs `.Call` C bridge for callbacks |
| C | [c.md](c.md) | C ABI + header facade | `--output` infers dir; CommissionType inverted |
| C# | [csharp.md](csharp.md) | C ABI P/Invoke | launch `dotnet <dll>`, not apphost |
| Julia | [julia.md](julia.md) | C ABI via Backtrader.jl | regex JSON extraction; `exectype=3` |
| Lua | [lua.md](lua.md) | C ABI C-host (no LuaJIT) | no FFI; `error()` in callback kills run |
| Node.js | [node.md](node.md) | N-API + libffi `btffi.node` | FMA bit-exactness is the expensive pitfall |
| Perl | [perl.md](perl.md) | SWIG only | no FFI::Platypus; Strawberry gcc consistency |
| PHP | [php.md](php.md) | FFI::cdef / SWIG | CData keep-alive; callbacks must not throw |
| Ruby | [ruby.md](ruby.md) | Fiddle / SWIG | `bt_strategy_create` unusable; use `..._callbacks` |
| Swift | [swift.md](swift.md) | C ABI clang module / SwiftPM | whole-module probe; no `-O`; one `@main` |
| Zig | [zig.md](zig.md) | `@import("backtrader")` typed pkg | `--abi` default trap; `toOwnedSlice` eval order |
| Python (SWIG) | [python_swig.md](python_swig.md) | SWIG facade | three-way audit vs py/pybind11/cpp |

## Capability boundary

These profiles document how real ports in `back_trader` are written. They do **not**
ship a runnable framework. All 14 ports depend on `back_trader`'s shared C ABI
(`libback_trader_c_abi`) or SWIG bindings plus per-language adapters/harnesses. If
that framework is not available, mark the port `scaffold-only` and do not claim parity.

If you have a different target framework, use the mapping tables and pitfall lists as
semantic guidance, then verify every API against that framework before running.

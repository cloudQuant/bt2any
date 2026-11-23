# Language Profiles

16 targets. Each profile lists: framework options, concept mapping from backtrader,
project layout, build/run commands, result emission, and language-specific pitfalls.
Profiles marked **scaffold** are partially filled — read them, then verify against
the actual target framework before claiming parity.

| Language | Profile | Status | Notes |
|---|---|---|---|
| C++ | [cpp.md](cpp.md) | detailed | Native frameworks or back_trader C++ core |
| Java | [java.md](java.md) | detailed | backtrader4j / custom engine / Spring service runner |
| Go | [go.md](go.md) | scaffold | C ABI bindings or native Go backtester |
| Rust | [rust.md](rust.md) | scaffold | C ABI facade / rustc rlib |
| R | [r.md](r.md) | scaffold | R runtime shim + C bridge |
| C | [c.md](c.md) | scaffold | C ABI core |
| C# | [csharp.md](csharp.md) | scaffold | .NET / C ABI |
| Julia | [julia.md](julia.md) | scaffold | ccall adapter |
| Lua | [lua.md](lua.md) | scaffold | FFI adapter |
| Node.js | [node.md](node.md) | scaffold | N-API / ffi-napi |
| Perl | [perl.md](perl.md) | scaffold | FFI::Platypus |
| PHP | [php.md](php.md) | scaffold | FFI |
| Ruby | [ruby.md](ruby.md) | scaffold | Fiddle |
| Swift | [swift.md](swift.md) | scaffold | C ABI module map |
| Zig | [zig.md](zig.md) | scaffold | @cImport C ABI |
| Python (SWIG) | [python_swig.md](python_swig.md) | scaffold | facade swap, not a true port |

"Detailed" means the mapping and pitfalls are filled; it does **not** mean a runnable
framework ships with this skill. Always state whether a real run was performed.

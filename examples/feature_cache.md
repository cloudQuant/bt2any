# Feature cache / external model

Load when: Read when Python preprocessing produces a cache used by the strategy.

## Python semantics
- Some runners precompute features (model predictions, normalization) into a file the
  strategy reads at runtime. This is external data, not strategy logic.
- The target may consume the same cache file. It must NOT replay decisions from the
  oracle's result — that is not a conversion.

## Target checklist
- [ ] cache file treated as immutable data input
- [ ] target computes signals from the same columns at the same bar
- [ ] cache path from config, not hardcoded
- [ ] document that the cache is an external dependency

## Failure signature
If the target cannot reproduce the cache, mark the port as dependent on that external
artifact; do not claim self-contained parity.

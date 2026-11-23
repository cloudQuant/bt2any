# Commission, margin and funding

Load when: Read when futures/perpetual semantics matter.

## Python semantics
- `percabs=True` => decimal-fraction commission (0.0004 = 0.04%). Different frameworks
  default differently — set it explicitly.
- `stocklike=True` => equity includes position market value; futures-like mode may book
  only margin and distort drawdown.
- Funding: rate × size × mark × mult; positive rate: longs pay, shorts receive.
  Many forks settle each bar using the previous bar's rate and mark (`[1]`).

## Target checklist
- [ ] commission expressed in the same unit (fraction vs percent)
- [ ] margin/stocklike mode matches the oracle
- [ ] funding uses previous-bar rate and mark, with the same fallback chain
- [ ] mark-price NaN fallback matches (e.g. fill with close)

## Failure signature
Equity diverges slowly with constant trade count → funding/commission compounding.

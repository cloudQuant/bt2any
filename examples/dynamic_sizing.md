# Dynamic sizing / target percent

Load when: Read when position size depends on equity.

## Python semantics
- Common pattern: `size = stake_pct * broker.getvalue() / price`. Equity at bar T is
  computed before submitting the order; the fill happens at T+1's open.
- Fixed notional vs dynamic equity are NOT interchangeable — they cause systematic
  divergence that grows with equity.

## Target checklist
- [ ] equity source matches (cash only vs cash+position value)
- [ ] size computed at the same bar as the oracle
- [ ] integer/lot rounding matches
- [ ] fee included/excluded consistently

## Failure signature
Trades align but final equity differs and the gap grows → sizing/compounding mismatch.

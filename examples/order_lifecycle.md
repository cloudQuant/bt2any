# Order lifecycle: stop / limit / OCO

Load when: Read when the strategy uses non-market orders.

## Python semantics
- Order status: Submitted → Accepted → Completed/Canceled/Margin/Rejected. `notify_order`
  sees each transition; only Completed changes position.
- Stop/limit fills depend on intrabar path. A naive `open->low->high->close` sequence
  overstates grid/mean-reversion strategies. Use the target framework's real fill model.
- OCO: one fill cancels the sibling; match the oracle's cancel semantics.

## Target checklist
- [ ] terminal-state guard clears the pending flag
- [ ] order role (open vs close) carried with the order, not inferred later
- [ ] intrabar fill order matches the oracle
- [ ] canceled orders do not leave phantom pending state

## Failure signature
Counts match but final_value diverges → likely fill price/timing, not signal logic.

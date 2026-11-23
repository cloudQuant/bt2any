# Example: Simple buy / sell / close

Load when: first conversion, or the strategy only enters/exits a single position.

## Python semantics to preserve

```python
def next(self):
    if self.order:            # pending-order guard: no new order while one is open
        return
    if not self.position:
        if self.data.close[0] > self.sma[0]:
            self.order = self.buy(size=100)
    else:
        if self.data.close[0] < self.sma[0]:
            self.order = self.close()
```

- Market order placed on bar T's close fills at bar T+1's open. Preserve the 1-bar lag.
- `self.order` is cleared in `notify_order` only on a terminal state (Completed /
  Canceled / Margin / Rejected), not on Submitted/Accepted.
- `self.close()` closes the entire open position; a plain `sell(size=...)` while long
  first reduces then flips — match the oracle.

## Target port shape

Every language profile must provide:
1. strategy class with start/next-equivalent hooks
2. pending-order flag cleared on terminal order callback
3. order API that respects next-bar-open fills
4. count extraction from the framework's trade results, not local increments

## Checklist

- [ ] `bar_num` matches oracle (date parse + minperiod)
- [ ] buy_count / sell_count from analyzer, with null preserved
- [ ] trade_num counts closed round-trips only
- [ ] final_value uses the same equity mode (include/exclude open PnL)
- [ ] result JSON has exactly the 11 fields

## Common failure

If counts are off by one, inspect the last bar: an order submitted on the final bar
may be filled after the oracle stops counting. Match the runner's date range exactly.

# Multi-timeframe, resample and replay

Load when: Read when the strategy uses multiple feeds or resampled data.

## Python semantics
- A slow indicator's value on the fast clock is the last CLOSED slow bar; reading the
  in-progress slow bar introduces look-ahead.
- Resample/replay can duplicate the tail bar or shift timestamps by one period.

## Target checklist
- [ ] first/last processed timestamps match the oracle
- [ ] slow-series value uses only closed bars on each fast bar
- [ ] no duplicated tail bar at the end
- [ ] `bar_num` counted the same way as the oracle runner

## Failure signature
`bar_num` mismatch → fix date/resample before debugging any trading logic.

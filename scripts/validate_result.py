#!/usr/bin/env python3
"""Validate a target-language result JSON against the Python oracle result.

Usage:
    python3 validate_result.py py_result.json results/<lang>_result.json

Exit 0 = parity passed; 1 = field/parity error; 2 = bad input.
Language-independent: this script only reads the 11-field contract.
"""
import json
import math
import sys

FIELDS = [
    "bar_num", "buy_count", "sell_count", "win_count", "loss_count",
    "trade_num", "final_value", "sharpe_ratio", "annual_return",
    "max_drawdown", "return_rate",
]
COUNT_FIELDS = {"bar_num", "buy_count", "sell_count", "win_count", "loss_count", "trade_num"}
EXTRA_ALLOWED = {
    "engine", "rows", "read_time_sec", "run_time_sec", "total_time_sec",
    "process_wall_time_sec", "results_time_sec", "strategy_function_time_sec",
    "sum_profit",
}
ALIAS = {"total_trades": "trade_num"}
TOL = 1e-6


def load(path):
    with open(path, encoding="utf-8") as f:
        d = json.load(f)
    # normalize aliases
    for src, dst in ALIAS.items():
        if src in d and dst not in d:
            d[dst] = d.pop(src)
    return d


def num_equal(a, b):
    if isinstance(a, bool) or isinstance(b, bool):
        return a == b
    if a is None or b is None:
        return a is None and b is None
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        if math.isnan(a) or math.isnan(b):
            return math.isnan(a) and math.isnan(b)
        if math.isinf(a) or math.isinf(b):
            return a == b
        if abs(a - b) <= TOL:
            return True
        scale = max(abs(a), abs(b), 1.0)
        return abs(a - b) / scale <= TOL
    return a == b


def main():
    if len(sys.argv) != 3:
        print("Usage: validate_result.py <py_result.json> <target_result.json>")
        return 2
    try:
        py, target = load(sys.argv[1]), load(sys.argv[2])
    except Exception as e:
        print(f"ERROR: cannot read JSON: {e}")
        return 2

    errs = []
    # illegal extra keys
    illegal = set(target) - set(FIELDS) - EXTRA_ALLOWED
    if illegal:
        errs.append(f"rejected_field_error: extra keys {sorted(illegal)}")
    # missing / null mismatches
    for k in FIELDS:
        if k not in py:
            errs.append(f"field_error: oracle missing {k}")
        if k not in target:
            errs.append(f"field_error: target missing {k}")
    if errs:
        for e in errs:
            print(e)
        return 1

    diffs = []
    for k in FIELDS:
        a, b = py[k], target[k]
        if k in COUNT_FIELDS and (a is None or b is None):
            ok = (a is None and b is None)
        else:
            ok = num_equal(a, b)
        if not ok:
            if isinstance(a, (int, float)) and isinstance(b, (int, float)) and a is not None and b is not None:
                d = abs(a - b)
                rel = d / max(abs(a), abs(b), 1.0)
                diffs.append(f"  {k}: py={a} target={b} abs={d:.3g} rel={rel:.3g}")
            else:
                diffs.append(f"  {k}: py={a!r} target={b!r}")

    if diffs:
        print("mismatched: fields differ beyond abs<=1e-6 or rel<=1e-6")
        print("\n".join(diffs))
        return 1

    print("matched: all 11 fields within tolerance")
    for k in FIELDS:
        print(f"  {k:14s} {py[k]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

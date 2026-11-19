"""Precision-aware last-digit extraction.

Deriv tick responses provide `quote` and `pip_size`. The pip size determines
the number of decimal places; the displayed quote is normalized to that
precision before extracting its final decimal digit.
"""
from decimal import Decimal, InvalidOperation
from typing import Any

class MalformedTick(ValueError):
    pass

def extract_last_digit(quote: Any, pip_size: Any) -> int:
    try:
        q = Decimal(str(quote))
        p = int(pip_size)
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise MalformedTick(f"invalid quote/pip_size: {quote!r}/{pip_size!r}") from exc
    if not q.is_finite() or p < 0 or p > 12:
        raise MalformedTick(f"unsupported quote or precision: {quote!r}/{pip_size!r}")
    rendered = f"{q:.{p}f}" if p else f"{q:.0f}"
    if p == 0:
        digit_char = rendered[-1]
    else:
        digit_char = rendered[-1]
    if digit_char not in "0123456789":
        raise MalformedTick(f"could not extract digit from normalized quote {rendered!r}")
    digit = int(digit_char)
    if not 0 <= digit <= 9:
        raise MalformedTick(f"digit out of range: {digit}")
    return digit

def tick_to_record(payload: dict) -> dict:
    tick = payload.get("tick", payload)
    if not isinstance(tick, dict) or "quote" not in tick or "pip_size" not in tick:
        raise MalformedTick("tick payload missing quote or pip_size")
    digit = extract_last_digit(tick["quote"], tick["pip_size"])
    return {
        "symbol": tick.get("symbol"),
        "quote": str(tick["quote"]),
        "pip_size": int(tick["pip_size"]),
        "epoch": tick.get("epoch"),
        "digit": digit,
    }

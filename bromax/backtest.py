from __future__ import annotations
import numpy as np
from scipy.stats import binomtest
from .agents import analyse

def backtest(digits, min_train=1000, step=1):
    """Expanding-window, strictly chronological one-step-ahead test.

    Only a signal computed from ticks before outcome t is scored. Abstentions
    remain abstentions and are reported separately (not counted as misses).
    """
    a = np.asarray(list(digits), dtype=int)
    if a.size and (np.any(a < 0) or np.any(a > 9)):
        raise ValueError("digits must be 0..9")
    hits = trials = abstentions = 0
    predictions = []
    for t in range(min_train, len(a), max(1, step)):
        result = analyse(a[:t], min_sample=min_train)["signal"]
        if not result["actionable"]:
            abstentions += 1
            continue
        trials += 1
        hit = int(result["digit"] == int(a[t]))
        hits += hit
        predictions.append({"index": t, "predicted": result["digit"],
                            "actual": int(a[t]), "hit": bool(hit)})
    rate = hits / trials if trials else None
    p = float(binomtest(hits, trials, 0.1, alternative="greater").pvalue) if trials else None
    return {"evaluated_ticks": max(0, len(a)-min_train), "signals_scored": trials,
            "abstentions": abstentions, "hits": hits, "hit_rate": rate,
            "baseline": 0.1, "p_value_vs_10_percent": p,
            "significant_at_0_05": bool(p is not None and p < 0.05),
            "predictions": predictions}

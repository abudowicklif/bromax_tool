from __future__ import annotations
import numpy as np
import pandas as pd
from scipy.stats import chisquare, binomtest, beta

BASELINE = 0.10

def _clean(digits):
    a = np.asarray(list(digits), dtype=int)
    if a.size and (np.any(a < 0) or np.any(a > 9)):
        raise ValueError("digits must be integers 0..9")
    return a

def frequency_analysis(digits):
    a = _clean(digits)
    n = int(a.size)
    counts = (pd.Series(a).value_counts().reindex(range(10), fill_value=0).to_numpy(dtype=int)
              if n else np.zeros(10, dtype=int))
    probs = counts / n if n else np.zeros(10)
    if n:
        chi, p = chisquare(counts, f_exp=np.full(10, n / 10))
    else:
        chi, p = 0.0, 1.0
    # Exact one-sided tests for each digit, Bonferroni family-wise correction.
    tests = []
    for d, k in enumerate(counts):
        raw = float(binomtest(int(k), n, BASELINE, alternative="greater").pvalue) if n else 1.0
        tests.append({"digit": d, "count": int(k), "rate": float(probs[d]),
                      "p_raw": raw, "p_adjusted": min(1.0, raw * 10)})
    return {"n": n, "counts": counts.tolist(), "probabilities": probs.tolist(),
            "chi_square": float(chi), "chi_square_p": float(p), "per_digit": tests}

def transition_analysis(digits):
    a = _clean(digits)
    if len(a) < 2:
        return {"n_transitions": 0, "best_after": None, "p_adjusted": 1.0,
                "matrix": np.zeros((10,10), dtype=int).tolist(), "finding": "insufficient data"}
    matrix = np.zeros((10,10), dtype=int)
    np.add.at(matrix, (a[:-1], a[1:]), 1)
    # Scan all 100 conditional cells vs 10% with Bonferroni correction.
    candidates = []
    for prev in range(10):
        row_n = int(matrix[prev].sum())
        if row_n < 30:
            continue
        for nxt in range(10):
            k = int(matrix[prev, nxt])
            p = float(binomtest(k, row_n, BASELINE, alternative="greater").pvalue)
            candidates.append((p, prev, nxt, k, row_n))
    if not candidates:
        return {"n_transitions": len(a)-1, "best_after": None, "p_adjusted": 1.0,
                "matrix": matrix.tolist(), "finding": "no adequately sampled transitions"}
    p, prev, nxt, k, row_n = min(candidates)
    adjusted = min(1.0, p * 100)
    return {"n_transitions": len(a)-1, "best_after": {"previous_digit": prev,
            "next_digit": nxt, "count": k, "row_n": row_n, "rate": k/row_n},
            "p_adjusted": adjusted, "matrix": matrix.tolist(),
            "finding": "candidate" if adjusted < 0.05 else "no corrected transition effect"}

def model_analysis(digits):
    """Jeffreys-smoothed categorical estimates with marginal 95% credible intervals."""
    a = _clean(digits)
    n = int(a.size)
    counts = np.bincount(a, minlength=10) if n else np.zeros(10, dtype=int)
    alpha = counts.astype(float) + 0.5
    total = float(alpha.sum())
    probs = alpha / total
    intervals = []
    for d in range(10):
        lo = float(beta.ppf(0.025, alpha[d], total-alpha[d]))
        hi = float(beta.ppf(0.975, alpha[d], total-alpha[d]))
        intervals.append([lo, hi])
    best = int(np.argmax(probs))
    return {"n": n, "probabilities": probs.tolist(), "intervals_95": intervals,
            "top_digit": best, "top_probability": float(probs[best]),
            "baseline": BASELINE,
            "note": "Intervals are marginal Jeffreys-prior credible intervals; not proof of predictability."}

def run_length_analysis(digits):
    a = _clean(digits)
    if len(a) < 2:
        return {"max_run": int(len(a)), "runs": 0}
    changes = np.r_[True, a[1:] != a[:-1]]
    starts = np.flatnonzero(changes)
    lengths = np.diff(np.r_[starts, len(a)])
    return {"max_run": int(lengths.max()), "runs": int(len(lengths))}

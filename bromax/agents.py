from .stats import frequency_analysis, transition_analysis, model_analysis, run_length_analysis

def analyse(digits, min_sample=1000):
    freq = frequency_analysis(digits)
    seq = transition_analysis(digits)
    model = model_analysis(digits)
    runs = run_length_analysis(digits)

    # Agents expose independently computed evidence; verifier controls admission.
    freq_candidates = [x for x in freq["per_digit"] if x["p_adjusted"] < 0.05]
    seq_candidate = seq.get("best_after") if seq["p_adjusted"] < 0.05 else None

    # Verifier rejects small samples, non-significant frequency evidence, and
    # sequence candidates that are not robustly corrected for 100 comparisons.
    accepted = []
    rejected = []
    if freq["n"] < min_sample:
        rejected.append({"agent": "frequency", "reason": f"sample below minimum ({freq['n']} < {min_sample})"})
    else:
        for item in freq_candidates:
            accepted.append({"agent": "frequency", "digit": item["digit"],
                             "p_adjusted": item["p_adjusted"], "rate": item["rate"]})
        if not freq_candidates:
            rejected.append({"agent": "frequency", "reason": "no digit beats 10% after Bonferroni correction"})
    if seq_candidate:
        accepted.append({"agent": "sequence", **seq_candidate, "p_adjusted": seq["p_adjusted"]})
    elif seq.get("best_after"):
        rejected.append({"agent": "sequence", "reason": "no transition survives 100-test correction"})
    else:
        rejected.append({"agent": "sequence", "reason": "insufficient transition observations"})

    # Signal requires at least one verifier-accepted digit and adequate n.
    # Sequence-only candidate is contextual, not a standalone unconditional digit forecast.
    signal_digit = None
    reason = "No actionable signal: no unconditional digit has verified evidence above the 10% baseline."
    if freq["n"] >= min_sample and freq_candidates:
        winner = min(freq_candidates, key=lambda x: x["p_adjusted"])
        signal_digit = int(winner["digit"])
        reason = "Frequency candidate passed the verifier's sample-size and corrected significance checks."
    confidence = "low"
    if signal_digit is not None:
        p = next(x["p_adjusted"] for x in freq_candidates if x["digit"] == signal_digit)
        confidence = "moderate" if p < 0.01 and freq["n"] >= 5000 else "low"
    return {
        "sample_size": freq["n"], "baseline_probability": 0.1,
        "agents": {
            "frequency": freq,
            "sequence": {**seq, "runs": runs},
            "statistical_model": model,
            "verification": {"accepted": accepted, "rejected": rejected,
                             "policy": "Bonferroni family-wise alpha=0.05; minimum sample enforced."}
        },
        "signal": {
            "actionable": signal_digit is not None,
            "digit": signal_digit,
            "estimated_probability": model["probabilities"][signal_digit] if signal_digit is not None else None,
            "uncertainty_95": model["intervals_95"][signal_digit] if signal_digit is not None else None,
            "confidence": confidence if signal_digit is not None else "none",
            "reason": reason,
            "dissent": rejected
        }
    }

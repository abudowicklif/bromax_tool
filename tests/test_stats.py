import numpy as np
from bromax.stats import frequency_analysis, transition_analysis, model_analysis, run_length_analysis

def test_frequency_uniform_counts():
    r=frequency_analysis(list(range(10))*100)
    assert r["n"] == 1000
    assert r["chi_square_p"] > .99

def test_frequency_skew_detected():
    r=frequency_analysis([0]*500+[1,2,3,4,5,6,7,8,9]*10)
    assert r["probabilities"][0] > .1
    assert r["per_digit"][0]["p_adjusted"] < .05

def test_model_probabilities_sum_to_one():
    r=model_analysis([1,1,2,3,4])
    assert abs(sum(r["probabilities"])-1)<1e-10
    assert len(r["intervals_95"])==10

def test_runs():
    assert run_length_analysis([1,1,1,2,2,3])["max_run"] == 3

def test_transition_matrix():
    r=transition_analysis([1,2,1,2,1,2]*20)
    assert sum(map(sum,r["matrix"])) == 119

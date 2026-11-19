from bromax.agents import analyse

def test_small_sample_abstains():
    r=analyse([0]*500, min_sample=1000)
    assert r["signal"]["actionable"] is False
    assert r["signal"]["digit"] is None
    assert r["agents"]["verification"]["rejected"]

def test_uniform_sample_does_not_force_signal():
    r=analyse(list(range(10))*150, min_sample=1000)
    assert r["signal"]["actionable"] is False

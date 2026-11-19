from bromax.backtest import backtest
import pytest

def test_backtest_counts_abstentions():
    r=backtest(list(range(10))*20, min_train=100)
    assert r["evaluated_ticks"] == 100
    assert r["signals_scored"] + r["abstentions"] == 100

def test_invalid_digits():
    with pytest.raises(ValueError): backtest([0,1,10], min_train=1)

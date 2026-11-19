import pytest
from bromax.digits import extract_last_digit, tick_to_record, MalformedTick

def test_precision_aware_digit():
    assert extract_last_digit("123.456", 3) == 6
    assert extract_last_digit("123.450", 3) == 0
    assert extract_last_digit("123.4", 2) == 0
    assert extract_last_digit("123", 0) == 3

def test_invalid_precision_and_quote():
    with pytest.raises(MalformedTick): extract_last_digit("nan", 2)
    with pytest.raises(MalformedTick): extract_last_digit("1.23", 20)

def test_tick_record():
    assert tick_to_record({"tick":{"quote":"12.39","pip_size":2}})["digit"] == 9

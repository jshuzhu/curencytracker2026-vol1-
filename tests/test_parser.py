import pytest
from currencybot.parser import parse_query

def test_full_query():
    q = parse_query("Convert 100 USD to MYR, SGD, and JPY")
    assert q.is_valid
    assert q.amount == 100.0
    assert q.source_currency == "USD"
    assert q.target_currencies == ["MYR", "SGD", "JPY"]

def test_shorthand_slang():
    q = parse_query("50 rm to bucks")
    assert q.is_valid
    assert q.amount == 50.0
    assert q.source_currency == "MYR"
    assert q.target_currencies == ["USD"]

def test_symbol_prefixed():
    q = parse_query("$250 to yen")
    assert q.is_valid
    assert q.amount == 250.0
    assert q.source_currency == "USD"
    assert q.target_currencies == ["JPY"]

def test_missing_amount():
    q = parse_query("USD to EUR")
    assert q.is_valid
    assert q.amount == 1.0
    assert q.source_currency == "USD"
    assert q.target_currencies == ["EUR"]

def test_missing_source():
    q = parse_query("to MYR")
    assert q.is_valid
    assert q.amount == 1.0
    assert q.source_currency == "USD"
    assert q.target_currencies == ["MYR"]

def test_missing_target():
    q = parse_query("100 EUR")
    assert q.is_valid
    assert q.amount == 100.0
    assert q.source_currency == "EUR"
    assert "USD" in q.target_currencies
    assert "MYR" in q.target_currencies

def test_sing_dollar():
    q = parse_query("100 sing dollar to rm")
    assert q.is_valid
    assert q.amount == 100.0
    assert q.source_currency == "SGD"
    assert q.target_currencies == ["MYR"]

def test_comma_numbers():
    q = parse_query("1,500.50 USD to MYR")
    assert q.is_valid
    assert q.amount == 1500.50
    assert q.source_currency == "USD"
    assert q.target_currencies == ["MYR"]

def test_invalid_empty():
    q = parse_query("")
    assert not q.is_valid

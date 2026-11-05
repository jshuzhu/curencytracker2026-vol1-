import pytest
from currencybot.converter import CurrencyConverter, format_amount, format_rate

def test_single_conversion_output_format():
    converter = CurrencyConverter()
    res = converter.process_query("100 USD to MYR")
    
    assert "Result Statement:" in res
    assert "100.00 USD =" in res
    assert "MYR" in res
    assert "Exchange Rate Summary:" in res
    assert "• Rate: 1 USD =" in res
    assert "• Last Updated:" in res
    assert "Quick Insights:" in res

def test_multi_target_output():
    converter = CurrencyConverter()
    res = converter.process_query("Convert 100 USD to MYR, SGD, and JPY")
    
    assert "Result Statement:" in res
    assert "MYR" in res
    assert "SGD" in res
    assert "JPY" in res
    assert "Exchange Rate Summary:" in res

def test_shorthand_output():
    converter = CurrencyConverter()
    res = converter.process_query("50 rm to bucks")
    assert "50.00 MYR =" in res
    assert "USD" in res

def test_default_amount_output():
    converter = CurrencyConverter()
    res = converter.process_query("EUR to USD")
    assert "1.00 EUR =" in res
    assert "USD" in res

def test_format_amount():
    assert format_amount(1234.56, "USD") == "1,234.56"
    assert format_amount(1234.0, "JPY") == "1,234"
    assert format_amount(5000000, "IDR") == "5,000,000"

def test_invalid_currency_clarification():
    converter = CurrencyConverter()
    res = converter.process_query("100 FOOBAR to USD")
    assert "Clarification needed" in res

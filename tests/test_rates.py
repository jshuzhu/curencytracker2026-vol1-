import pytest
from currencybot.rates_service import RatesService

def test_live_or_cached_rates():
    service = RatesService()
    res = service.get_rate("USD", "MYR")
    assert res.source == "USD"
    assert res.target == "MYR"
    assert res.rate > 0
    assert len(res.last_updated) > 0

def test_cross_rates():
    service = RatesService()
    res = service.get_rate("MYR", "JPY")
    assert res.source == "MYR"
    assert res.target == "JPY"
    assert res.rate > 0

def test_identity_rate():
    service = RatesService()
    res = service.get_rate("USD", "USD")
    assert res.rate == 1.0

def test_unsupported_currency():
    service = RatesService()
    with pytest.raises(ValueError, match="Unsupported or unknown"):
        service.get_rate("XYZABC", "USD")

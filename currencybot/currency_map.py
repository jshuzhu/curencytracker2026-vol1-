"""
Currency aliases, symbols, and standard ISO codes mapping.
"""

from typing import Optional, Dict

# Standard names for major currencies
CURRENCY_NAMES: Dict[str, str] = {
    "USD": "United States Dollar",
    "EUR": "Euro",
    "MYR": "Malaysian Ringgit",
    "SGD": "Singapore Dollar",
    "JPY": "Japanese Yen",
    "GBP": "British Pound",
    "AUD": "Australian Dollar",
    "CAD": "Canadian Dollar",
    "CHF": "Swiss Franc",
    "CNY": "Chinese Yuan",
    "HKD": "Hong Kong Dollar",
    "NZD": "New Zealand Dollar",
    "INR": "Indian Rupee",
    "KRW": "South Korean Won",
    "THB": "Thai Baht",
    "IDR": "Indonesian Rupiah",
    "PHP": "Philippine Peso",
    "VND": "Vietnamese Dong",
    "TWD": "New Taiwan Dollar",
    "AED": "UAE Dirham",
    "SAR": "Saudi Riyal",
    "BRL": "Brazilian Real",
    "MXN": "Mexican Peso",
    "ZAR": "South African Rand",
    "TRY": "Turkish Lira",
    "SEK": "Swedish Krona",
    "NOK": "Norwegian Krone",
    "DKK": "Danish Krone",
    "PLN": "Polish Zloty",
}

# Slang, colloquial terms, symbols, and aliases mapping to 3-letter ISO code
CURRENCY_ALIASES: Dict[str, str] = {
    # Symbols
    "$": "USD",
    "US$": "USD",
    "€": "EUR",
    "£": "GBP",
    "¥": "JPY",
    "₹": "INR",
    "₩": "KRW",
    "฿": "THB",
    "₫": "VND",
    "₱": "PHP",
    "₺": "TRY",
    "R$": "BRL",
    "A$": "AUD",
    "AU$": "AUD",
    "C$": "CAD",
    "CA$": "CAD",
    "S$": "SGD",
    "SG$": "SGD",
    "NZ$": "NZD",
    "HK$": "HKD",

    # Malaysian Ringgit
    "rm": "MYR",
    "ringgit": "MYR",
    "malaysian ringgit": "MYR",
    "myr": "MYR",

    # United States Dollar
    "usd": "USD",
    "dollar": "USD",
    "dollars": "USD",
    "buck": "USD",
    "bucks": "USD",
    "us dollar": "USD",
    "greenback": "USD",
    "greenbacks": "USD",

    # Singapore Dollar
    "sgd": "SGD",
    "sing dollar": "SGD",
    "singapore dollar": "SGD",
    "sing dollars": "SGD",

    # Japanese Yen
    "jpy": "JPY",
    "yen": "JPY",
    "japanese yen": "JPY",

    # British Pound
    "gbp": "GBP",
    "pound": "GBP",
    "pounds": "GBP",
    "quid": "GBP",
    "sterling": "GBP",
    "british pound": "GBP",
    "great british pound": "GBP",

    # Euro
    "eur": "EUR",
    "euro": "EUR",
    "euros": "EUR",

    # Australian Dollar
    "aud": "AUD",
    "aussie": "AUD",
    "aussie dollar": "AUD",
    "australian dollar": "AUD",

    # Canadian Dollar
    "cad": "CAD",
    "loonie": "CAD",
    "canadian dollar": "CAD",

    # Swiss Franc
    "chf": "CHF",
    "franc": "CHF",
    "francs": "CHF",
    "swiss franc": "CHF",

    # Chinese Yuan
    "cny": "CNY",
    "yuan": "CNY",
    "rmb": "CNY",
    "renminbi": "CNY",
    "chinese yuan": "CNY",

    # Indian Rupee
    "inr": "INR",
    "rupee": "INR",
    "rupees": "INR",
    "indian rupee": "INR",

    # South Korean Won
    "krw": "KRW",
    "won": "KRW",
    "korean won": "KRW",

    # Thai Baht
    "thb": "THB",
    "baht": "THB",
    "thai baht": "THB",

    # Indonesian Rupiah
    "idr": "IDR",
    "rupiah": "IDR",
    "indonesian rupiah": "IDR",

    # Philippine Peso
    "php": "PHP",
    "philippine peso": "PHP",

    # Mexican Peso
    "mxn": "MXN",
    "mexican peso": "MXN",
    "peso": "MXN",
    "pesos": "MXN",

    # Hong Kong Dollar
    "hkd": "HKD",
    "hong kong dollar": "HKD",

    # New Zealand Dollar
    "nzd": "NZD",
    "kiwi": "NZD",
    "new zealand dollar": "NZD",

    # Vietnamese Dong
    "vnd": "VND",
    "dong": "VND",
    "vietnamese dong": "VND",

    # Taiwan Dollar
    "twd": "TWD",
    "ntd": "TWD",
    "taiwan dollar": "TWD",
    "new taiwan dollar": "TWD",

    # Middle East
    "aed": "AED",
    "dirham": "AED",
    "uae dirham": "AED",
    "sar": "SAR",
    "riyal": "SAR",
    "saudi riyal": "SAR",
    "ils": "ILS",
    "shekel": "ILS",

    # Scandinavian
    "sek": "SEK",
    "krona": "SEK",
    "swedish krona": "SEK",
    "nok": "NOK",
    "krone": "NOK",
    "norwegian krone": "NOK",
    "dkk": "DKK",
    "danish krone": "DKK",

    # Other Major
    "try": "TRY",
    "lira": "TRY",
    "turkish lira": "TRY",
    "zar": "ZAR",
    "rand": "ZAR",
    "south african rand": "ZAR",
    "pln": "PLN",
    "zloty": "PLN",
    "brl": "BRL",
    "real": "BRL",
    "brazilian real": "BRL",
}


COMMON_NON_CURRENCY_WORDS = {
    "and", "the", "for", "out", "can", "are", "not", "yes", "all", "now",
    "our", "per", "via", "any", "how", "who", "why", "let", "see", "get",
    "was", "one", "two", "ten", "few"
}


def normalize_currency(term: str) -> Optional[str]:
    """
    Normalizes a currency code, abbreviation, symbol, or slang to standard 3-letter ISO code.
    Returns uppercase 3-letter ISO string, or None if unrecognized.
    """
    if not term:
        return None
    cleaned = term.strip().lower()

    if cleaned in COMMON_NON_CURRENCY_WORDS:
        return None
    
    # Check alias dictionary
    if cleaned in CURRENCY_ALIASES:
        return CURRENCY_ALIASES[cleaned]
    
    # Check if direct 3-letter code
    upper = term.strip().upper()
    if len(upper) == 3 and upper.isalpha():
        return upper

    return None

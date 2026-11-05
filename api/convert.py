"""
Vercel serverless function: /api/convert?q=...
"""

from http.server import BaseHTTPRequestHandler
import json
import urllib.parse
import urllib.request
import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field


# ── Currency Aliases ──────────────────────────────────────────────────────

COMMON_NON_CURRENCY_WORDS = {
    "and", "the", "for", "out", "can", "are", "not", "yes", "all", "now",
    "our", "per", "via", "any", "how", "who", "why", "let", "see", "get",
    "was", "one", "two", "ten", "few"
}

CURRENCY_ALIASES: Dict[str, str] = {
    "$": "USD", "US$": "USD", "€": "EUR", "£": "GBP", "¥": "JPY",
    "₹": "INR", "₩": "KRW", "฿": "THB", "₫": "VND", "₱": "PHP",
    "₺": "TRY", "R$": "BRL", "A$": "AUD", "AU$": "AUD", "C$": "CAD",
    "CA$": "CAD", "S$": "SGD", "SG$": "SGD", "NZ$": "NZD", "HK$": "HKD",
    "rm": "MYR", "ringgit": "MYR", "malaysian ringgit": "MYR", "myr": "MYR",
    "usd": "USD", "dollar": "USD", "dollars": "USD", "buck": "USD",
    "bucks": "USD", "us dollar": "USD", "greenback": "USD", "greenbacks": "USD",
    "sgd": "SGD", "sing dollar": "SGD", "singapore dollar": "SGD", "sing dollars": "SGD",
    "jpy": "JPY", "yen": "JPY", "japanese yen": "JPY",
    "gbp": "GBP", "pound": "GBP", "pounds": "GBP", "quid": "GBP",
    "sterling": "GBP", "british pound": "GBP",
    "eur": "EUR", "euro": "EUR", "euros": "EUR",
    "aud": "AUD", "aussie": "AUD", "aussie dollar": "AUD", "australian dollar": "AUD",
    "cad": "CAD", "loonie": "CAD", "canadian dollar": "CAD",
    "chf": "CHF", "franc": "CHF", "francs": "CHF", "swiss franc": "CHF",
    "cny": "CNY", "yuan": "CNY", "rmb": "CNY", "renminbi": "CNY", "chinese yuan": "CNY",
    "inr": "INR", "rupee": "INR", "rupees": "INR", "indian rupee": "INR",
    "krw": "KRW", "won": "KRW", "korean won": "KRW",
    "thb": "THB", "baht": "THB", "thai baht": "THB",
    "idr": "IDR", "rupiah": "IDR", "indonesian rupiah": "IDR",
    "php": "PHP", "philippine peso": "PHP",
    "mxn": "MXN", "mexican peso": "MXN", "peso": "MXN", "pesos": "MXN",
    "hkd": "HKD", "hong kong dollar": "HKD",
    "nzd": "NZD", "kiwi": "NZD", "new zealand dollar": "NZD",
    "vnd": "VND", "dong": "VND", "vietnamese dong": "VND",
    "twd": "TWD", "ntd": "TWD", "taiwan dollar": "TWD",
    "aed": "AED", "dirham": "AED", "uae dirham": "AED",
    "sar": "SAR", "riyal": "SAR", "saudi riyal": "SAR",
    "sek": "SEK", "krona": "SEK", "swedish krona": "SEK",
    "nok": "NOK", "krone": "NOK", "norwegian krone": "NOK",
    "dkk": "DKK", "danish krone": "DKK",
    "try": "TRY", "lira": "TRY", "turkish lira": "TRY",
    "zar": "ZAR", "rand": "ZAR", "south african rand": "ZAR",
    "pln": "PLN", "zloty": "PLN",
    "brl": "BRL", "real": "BRL", "brazilian real": "BRL",
}

FILLER_WORDS = {
    "please", "can", "you", "convert", "exchange", "calculate", "how", "much",
    "is", "what", "rate", "of", "the", "in", "to", "into", "as", "from",
    "and", "a", "an", "value", "for", "with"
}

ZERO_DECIMAL = {"JPY", "KRW", "VND", "IDR", "CLP", "HUF", "PYG", "UGX"}


def normalize_currency(term: str) -> Optional[str]:
    if not term:
        return None
    cleaned = term.strip().lower()
    if cleaned in COMMON_NON_CURRENCY_WORDS:
        return None
    if cleaned in CURRENCY_ALIASES:
        return CURRENCY_ALIASES[cleaned]
    upper = term.strip().upper()
    if len(upper) == 3 and upper.isalpha():
        return upper
    return None


# ── Parser ────────────────────────────────────────────────────────────────

@dataclass
class ParsedQuery:
    amount: float
    source_currency: str
    target_currencies: List[str]
    is_valid: bool = True
    error_message: Optional[str] = None
    notes: List[str] = field(default_factory=list)


def _clean_text(text: str) -> str:
    t = text.strip()
    for p in [r"^(?:please\s+)?(?:can\s+you\s+)?convert\s+", r"^how\s+much\s+is\s+",
              r"^what\s+is\s+", r"^exchange\s+", r"^calculate\s+", r"^rate\s+of\s+"]:
        t = re.sub(p, "", t, flags=re.IGNORECASE).strip()
    return t


def _extract_amount(text: str) -> Tuple[Optional[float], str]:
    match = re.search(r"(?<![a-zA-Z])(?:\$|€|£|¥|₹|₩|฿|₫|₱|₺|RM|rm)?\s*([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]+)?|[0-9]+(?:\.[0-9]+)?)\b", text)
    if match:
        try:
            val = float(match.group(1).replace(",", ""))
            return val, text[:match.start(1)] + text[match.end(1):]
        except ValueError:
            pass
    return None, text


def _extract_currencies_and_unrecognized(text: str) -> Tuple[List[str], List[str]]:
    cleaned = re.sub(r"[,/&]", " ", text)
    tokens = cleaned.split()
    found, unrecognized = [], []
    i = 0
    while i < len(tokens):
        tok = tokens[i].strip()
        if not tok:
            i += 1
            continue
        matched = False
        for length in (3, 2, 1):
            if i + length <= len(tokens):
                phrase = " ".join(tokens[i:i+length]).strip().lower()
                iso = normalize_currency(phrase)
                if iso:
                    if iso not in found:
                        found.append(iso)
                    i += length
                    matched = True
                    break
        if not matched:
            clean_word = re.sub(r"[^A-Za-z]", "", tok.lower())
            if clean_word and clean_word not in FILLER_WORDS:
                unrecognized.append(tok)
            i += 1
    return found, unrecognized


def parse_query(raw_query: str) -> ParsedQuery:
    if not raw_query or not raw_query.strip():
        return ParsedQuery(1.0, "USD", [], is_valid=False, error_message="Please enter a query.")

    text = _clean_text(raw_query)
    notes: List[str] = []

    symbol_source = None
    sym_match = re.search(r"(\$|€|£|¥|₹|₩|฿|₫|₱|₺|RM|rm)\s*[0-9]", text)
    if sym_match:
        symbol_source = normalize_currency(sym_match.group(1))

    amount, text_without_amount = _extract_amount(text)
    if amount is None:
        amount = 1.0
        notes.append("Amount defaulted to 1.")
    elif amount <= 0:
        return ParsedQuery(amount, "USD", [], is_valid=False, error_message="Amount must be > 0.")

    sep_match = re.search(r"\b(?:to|in|into|as|\->|=>)\b", text_without_amount, flags=re.IGNORECASE)

    if sep_match:
        left = text_without_amount[:sep_match.start()].strip()
        right = text_without_amount[sep_match.end():].strip()
        src_cands, left_unrec = _extract_currencies_and_unrecognized(left)
        if left_unrec:
            return ParsedQuery(amount, "USD", [], is_valid=False,
                               error_message=f"Unrecognized currency '{left_unrec[0]}'.")
        source_curr = src_cands[0] if src_cands else (symbol_source or "USD")
        if not src_cands and not symbol_source:
            notes.append("Source defaulted to USD.")
        targets, right_unrec = _extract_currencies_and_unrecognized(right)
        if right_unrec:
            return ParsedQuery(amount, source_curr, [], is_valid=False,
                               error_message=f"Unrecognized target currency '{right_unrec[0]}'.")
    else:
        all_c, unrec = _extract_currencies_and_unrecognized(text_without_amount)
        if symbol_source and symbol_source not in all_c:
            all_c.insert(0, symbol_source)
        if unrec:
            return ParsedQuery(amount, "USD", [], is_valid=False,
                               error_message=f"Unrecognized currency '{unrec[0]}'.")
        if len(all_c) == 0:
            source_curr, targets = "USD", []
        elif len(all_c) == 1:
            source_curr, targets = all_c[0], []
        else:
            source_curr, targets = all_c[0], all_c[1:]

    if not targets:
        targets = [c for c in ["USD", "MYR", "EUR", "SGD"] if c != source_curr][:3]
        notes.append(f"Target defaulted to {', '.join(targets)}.")

    deduped = []
    for t in targets:
        if t not in deduped and t != source_curr:
            deduped.append(t)

    return ParsedQuery(amount, source_curr, deduped or [source_curr], is_valid=True, notes=notes)


# ── Rates fetching ────────────────────────────────────────────────────────

def fetch_rates() -> Tuple[Dict[str, float], str]:
    try:
        req = urllib.request.Request("https://open.er-api.com/v6/latest/USD",
                                     headers={"User-Agent": "CurrencyBot/1.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data.get("result") == "success":
                rates = data["rates"]
                rates["USD"] = 1.0
                return rates, data.get("time_last_update_utc", "Unknown")
    except Exception:
        pass
    try:
        req = urllib.request.Request("https://api.frankfurter.dev/v1/latest?base=USD",
                                     headers={"User-Agent": "CurrencyBot/1.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if "rates" in data:
                rates = data["rates"]
                rates["USD"] = 1.0
                return rates, data.get("date", "Unknown")
    except Exception:
        pass
    return {}, "Unavailable"


# ── Formatter ─────────────────────────────────────────────────────────────

def fmt_amount(val: float, code: str) -> str:
    if code in ZERO_DECIMAL and val == int(val):
        return f"{int(val):,}"
    return f"{val:,.2f}"

def fmt_rate(rate: float) -> str:
    if rate >= 100: return f"{rate:,.2f}"
    if rate >= 0.0001: return f"{rate:,.4f}"
    return f"{rate:,.6f}"


def do_convert(query: str) -> dict:
    parsed = parse_query(query)
    if not parsed.is_valid:
        return {"success": False, "query": query, "formatted_output": f"Clarification needed: {parsed.error_message}"}

    rates, updated = fetch_rates()
    if not rates:
        return {"success": False, "query": query, "formatted_output": "Unable to retrieve exchange rates. Please try again."}

    src = parsed.source_currency
    if src not in rates:
        return {"success": False, "query": query,
                "formatted_output": f"Clarification needed: Unsupported currency '{src}'."}

    lines = ["Result Statement:"]
    rate_lines = []
    inv_parts = []

    for tgt in parsed.target_currencies:
        if tgt not in rates:
            return {"success": False, "query": query,
                    "formatted_output": f"Clarification needed: Unsupported currency '{tgt}'."}
        rate = rates[tgt] / rates[src]
        converted = parsed.amount * rate
        inv = 1.0 / rate if rate else 0

        lines.append(f"{fmt_amount(parsed.amount, src)} {src} = {fmt_amount(converted, tgt)} {tgt}")
        rate_lines.append(f"* Rate: 1 {src} = {fmt_rate(rate)} {tgt}")
        inv_parts.append(f"1 {tgt} = {fmt_rate(inv)} {src}")

    lines.append("")
    lines.append("Exchange Rate Summary:")
    lines.extend(rate_lines)
    lines.append(f"* Last Updated: {updated}")
    lines.append("")
    lines.append("Quick Insights:")
    lines.append(f"* Inverse: {' | '.join(inv_parts)}")

    return {"success": True, "query": query, "formatted_output": "\n".join(lines)}


# ── Vercel Handler ────────────────────────────────────────────────────────

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        query = params.get("q", [""])[0]

        result = do_convert(query)
        body = json.dumps(result, indent=2).encode("utf-8")

        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

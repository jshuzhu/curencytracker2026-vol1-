"""
Natural language and shorthand query parser for CurrencyBot.
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Tuple
from currencybot.currency_map import normalize_currency

@dataclass
class ParsedQuery:
    amount: float
    source_currency: str
    target_currencies: List[str]
    raw_query: str
    is_valid: bool = True
    error_message: Optional[str] = None
    notes: List[str] = field(default_factory=list)


# Standard major currencies to fall back to when targets are not specified
DEFAULT_MAJOR_TARGETS = ["USD", "MYR", "EUR", "SGD", "GBP", "JPY"]

# Common filler/stop words that can appear around currency queries
FILLER_WORDS = {
    "please", "can", "you", "convert", "exchange", "calculate", "how", "much", "is",
    "what", "rate", "of", "the", "in", "to", "into", "as", "from", "and", "a", "an",
    "value", "for", "with"
}


def _clean_text(text: str) -> str:
    """Removes common conversational prefixes and cleans whitespace."""
    t = text.strip()
    prefixes = [
        r"^(?:please\s+)?(?:can\s+you\s+)?convert\s+",
        r"^how\s+much\s+is\s+",
        r"^what\s+is\s+",
        r"^exchange\s+",
        r"^calculate\s+",
        r"^rate\s+of\s+",
    ]
    for p in prefixes:
        t = re.sub(p, "", t, flags=re.IGNORECASE).strip()
    return t


def _extract_amount(text: str) -> Tuple[Optional[float], str]:
    """
    Extracts numerical amount (including commas, e.g., 1,000.50).
    Returns (amount, remaining_text).
    """
    match = re.search(r"(?<![a-zA-Z])(?:\$|€|£|¥|₹|₩|฿|₫|₱|₺|RM|rm)?\s*([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]+)?|[0-9]+(?:\.[0-9]+)?)\b", text)
    if match:
        raw_num = match.group(1).replace(",", "")
        try:
            val = float(raw_num)
            rem = text[:match.start(1)] + text[match.end(1):]
            return val, rem
        except ValueError:
            pass
    return None, text


def _extract_currencies_and_unrecognized(text: str) -> Tuple[List[str], List[str]]:
    """
    Finds and resolves currency aliases/codes within a segment of text.
    Correctly recognizes multi-word aliases (e.g. 'sing dollar', 'us dollar')
    and returns unrecognized words that are not filler words.
    """
    cleaned = re.sub(r"[,/&]", " ", text)
    tokens = cleaned.split()
    
    found: List[str] = []
    unrecognized: List[str] = []
    
    i = 0
    while i < len(tokens):
        tok = tokens[i].strip()
        lower_tok = tok.lower()

        # Skip empty or symbols already stripped
        if not tok:
            i += 1
            continue

        matched = False
        # Try multi-word aliases first by sliding window (3, 2, 1)
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
            clean_word = re.sub(r"[^A-Za-z]", "", lower_tok)
            if clean_word and clean_word not in FILLER_WORDS:
                unrecognized.append(tok)
            i += 1
            
    return found, unrecognized


def parse_query(raw_query: str) -> ParsedQuery:
    """
    Parses a user input string into a structured ParsedQuery object.
    """
    if not raw_query or not raw_query.strip():
        return ParsedQuery(
            amount=1.0,
            source_currency="USD",
            target_currencies=["MYR", "EUR"],
            raw_query="",
            is_valid=False,
            error_message="Please enter a currency conversion query (e.g., '100 USD to MYR' or '50 rm to usd')."
        )
    
    text = _clean_text(raw_query)
    notes: List[str] = []

    # Detect symbol prefixed/attached to amount before stripping (e.g. $100, RM50, €20, £50, ¥1000)
    symbol_source = None
    sym_match = re.search(r"(\$|€|£|¥|₹|₩|฿|₫|₱|₺|RM|rm)\s*[0-9]", text)
    if sym_match:
        sym = sym_match.group(1)
        symbol_source = normalize_currency(sym)

    # Extract numerical amount
    amount, text_without_amount = _extract_amount(text)
    if amount is None:
        amount = 1.0
        notes.append("Amount was not specified; defaulted to 1.")
    elif amount <= 0:
        return ParsedQuery(
            amount=amount,
            source_currency="USD",
            target_currencies=[],
            raw_query=raw_query,
            is_valid=False,
            error_message="Amount must be greater than zero."
        )

    # Check for directional keywords ("to", "in", "into", "->", "=>")
    sep_match = re.search(r"\b(?:to|in|into|as|\->|=>)\b", text_without_amount, flags=re.IGNORECASE)
    
    if sep_match:
        left_side = text_without_amount[:sep_match.start()].strip()
        right_side = text_without_amount[sep_match.end():].strip()
        
        # Source is on the left
        source_candidates, left_unrec = _extract_currencies_and_unrecognized(left_side)
        if left_unrec:
            return ParsedQuery(
                amount=amount,
                source_currency="USD",
                target_currencies=[],
                raw_query=raw_query,
                is_valid=False,
                error_message=f"Unrecognized or invalid currency '{left_unrec[0]}'. Please clarify or use a standard currency code (e.g., USD, MYR, EUR, JPY)."
            )

        if not source_candidates and symbol_source:
            source_curr = symbol_source
        elif source_candidates:
            source_curr = source_candidates[0]
        else:
            source_curr = "USD"
            notes.append("Source currency not specified; defaulted to USD.")
            
        # Targets are on the right
        targets, right_unrec = _extract_currencies_and_unrecognized(right_side)
        if right_unrec:
            return ParsedQuery(
                amount=amount,
                source_currency=source_curr,
                target_currencies=[],
                raw_query=raw_query,
                is_valid=False,
                error_message=f"Unrecognized or invalid target currency '{right_unrec[0]}'. Please clarify or use a standard currency code (e.g., USD, MYR, EUR, JPY)."
            )
    else:
        # No directional separator; extract all currencies mentioned
        all_currencies, unrec = _extract_currencies_and_unrecognized(text_without_amount)
        if symbol_source and symbol_source not in all_currencies:
            all_currencies.insert(0, symbol_source)

        if unrec:
            return ParsedQuery(
                amount=amount,
                source_currency="USD",
                target_currencies=[],
                raw_query=raw_query,
                is_valid=False,
                error_message=f"Unrecognized or invalid currency '{unrec[0]}'. Please clarify or use a standard currency code (e.g., USD, MYR, EUR, JPY)."
            )
            
        if len(all_currencies) == 0:
            source_curr = "USD"
            targets = []
            notes.append("Source currency defaulted to USD.")
        elif len(all_currencies) == 1:
            # Single currency provided (e.g. "100 EUR" or "MYR")
            source_curr = all_currencies[0]
            targets = []
        else:
            # Multiple currencies: first is source, rest are targets
            source_curr = all_currencies[0]
            targets = all_currencies[1:]

    # If targets are missing, select default major currencies excluding source
    if not targets:
        default_targets = [c for c in ["USD", "MYR", "EUR", "SGD"] if c != source_curr][:3]
        targets = default_targets
        notes.append(f"Target currency not specified; defaulted to {', '.join(targets)}.")

    # Deduplicate targets while preserving order
    deduped_targets = []
    for t in targets:
        if t not in deduped_targets and t != source_curr:
            deduped_targets.append(t)

    if not deduped_targets:
        # In case user asked "USD to USD"
        return ParsedQuery(
            amount=amount,
            source_currency=source_curr,
            target_currencies=[source_curr],
            raw_query=raw_query,
            is_valid=True,
            notes=notes
        )

    return ParsedQuery(
        amount=amount,
        source_currency=source_curr,
        target_currencies=deduped_targets,
        raw_query=raw_query,
        is_valid=True,
        notes=notes
    )

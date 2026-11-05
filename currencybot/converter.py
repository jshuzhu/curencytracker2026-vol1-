"""
Core conversion engine, mathematical precision formatting, and insight generation.
"""

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Optional
from currencybot.parser import parse_query, ParsedQuery
from currencybot.rates_service import RatesService, RateResult

# Currencies that typically don't use decimal sub-units (or commonly displayed as whole)
ZERO_DECIMAL_CURRENCIES = {"JPY", "KRW", "VND", "IDR", "CLP", "HUF", "PYG", "UGX"}


def format_amount(amount: float, currency_code: str) -> str:
    """Formats amount with appropriate thousands commas and decimal precision."""
    curr = currency_code.upper()
    if curr in ZERO_DECIMAL_CURRENCIES:
        if amount == int(amount):
            return f"{int(amount):,}"
        return f"{amount:,.2f}"
    return f"{amount:,.2f}"


def format_rate(rate: float) -> str:
    """Formats exchange rate with appropriate decimal precision (at least 4 decimals)."""
    if rate >= 1000:
        return f"{rate:,.2f}"
    elif rate >= 100:
        return f"{rate:,.3f}"
    elif rate >= 0.0001:
        return f"{rate:,.4f}"
    else:
        return f"{rate:,.6f}"


@dataclass
class TargetConversion:
    target_currency: str
    rate: float
    converted_amount: float
    formatted_amount: str
    formatted_rate: str
    inverse_rate: float
    formatted_inverse_rate: str


@dataclass
class ConversionOutput:
    source_currency: str
    amount: float
    formatted_source_amount: str
    conversions: List[TargetConversion]
    last_updated: str
    is_cached: bool
    disclaimer: Optional[str]
    notes: List[str]

    def to_formatted_text(self, include_insights: bool = True) -> str:
        """Renders the output conforming strictly to CurrencyBot specifications."""
        lines: List[str] = []

        # Result Statement
        lines.append("Result Statement:")
        for conv in self.conversions:
            lines.append(f"{self.formatted_source_amount} {self.source_currency} = {conv.formatted_amount} {conv.target_currency}")
        
        lines.append("")

        # Exchange Rate Summary
        lines.append("Exchange Rate Summary:")
        for conv in self.conversions:
            lines.append(f"• Rate: 1 {self.source_currency} = {conv.formatted_rate} {conv.target_currency}")
        lines.append(f"• Last Updated: {self.last_updated}")
        
        if self.is_cached and self.disclaimer:
            lines.append(f"• Note: {self.disclaimer}")

        # Optional Quick Insights
        if include_insights:
            lines.append("")
            lines.append("Quick Insights:")
            # Inverse rate insight
            inv_parts = [f"1 {c.target_currency} = {c.formatted_inverse_rate} {self.source_currency}" for c in self.conversions]
            lines.append(f"• Inverse: {' | '.join(inv_parts)}")
            
            # Rounded breakdown insight
            rounded_parts = [f"{round(c.converted_amount):,} {c.target_currency}" for c in self.conversions]
            if len(self.conversions) == 1:
                lines.append(f"• Rounded: {round(self.amount):,} {self.source_currency} is approximately {rounded_parts[0]}.")
            else:
                lines.append(f"• Rounded: {round(self.amount):,} {self.source_currency} is approximately {', '.join(rounded_parts)}.")

        return "\n".join(lines)


class CurrencyConverter:
    def __init__(self, rates_service: Optional[RatesService] = None):
        self.rates_service = rates_service or RatesService()

    def process_query(self, raw_query: str) -> str:
        """
        Processes a natural language or shorthand query and returns formatted response.
        """
        parsed = parse_query(raw_query)
        if not parsed.is_valid:
            return f"Clarification needed: {parsed.error_message}"

        return self.convert(
            amount=parsed.amount,
            source=parsed.source_currency,
            targets=parsed.target_currencies,
            notes=parsed.notes,
        )

    def convert(
        self,
        amount: float,
        source: str,
        targets: List[str],
        notes: Optional[List[str]] = None,
        include_insights: bool = True
    ) -> str:
        """
        Performs the conversion calculation and returns strict formatted text.
        """
        notes = notes or []
        conversions: List[TargetConversion] = []
        last_updated_str = ""
        is_cached = False
        disclaimer = None

        try:
            for target in targets:
                rate_result = self.rates_service.get_rate(source, target)
                converted_val = amount * rate_result.rate
                inv_rate = 1.0 / rate_result.rate if rate_result.rate != 0 else 0.0

                conversions.append(
                    TargetConversion(
                        target_currency=target,
                        rate=rate_result.rate,
                        converted_amount=converted_val,
                        formatted_amount=format_amount(converted_val, target),
                        formatted_rate=format_rate(rate_result.rate),
                        inverse_rate=inv_rate,
                        formatted_inverse_rate=format_rate(inv_rate),
                    )
                )
                last_updated_str = rate_result.last_updated
                if rate_result.is_cached:
                    is_cached = True
                    disclaimer = rate_result.disclaimer

        except ValueError as e:
            return f"Clarification needed: {str(e)}"
        except Exception as e:
            return f"Unable to retrieve exchange rates at this time: {str(e)}"

        output = ConversionOutput(
            source_currency=source.upper(),
            amount=amount,
            formatted_source_amount=format_amount(amount, source),
            conversions=conversions,
            last_updated=last_updated_str,
            is_cached=is_cached,
            disclaimer=disclaimer,
            notes=notes,
        )

        return output.to_formatted_text(include_insights=include_insights)

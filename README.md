# CurrencyBot 💱

A lightweight, fast, and accurate Currency Converter AI Assistant built for real-time rates, natural language queries, multi-currency conversions, and graceful offline fallback.

---

## Features

- **Natural Language & Shorthand Parsing**:
  - Handles symbols (`$`, `€`, `£`, `¥`, `RM`, `₹`, `₩`, etc.) and slang (`rm` $\rightarrow$ MYR, `bucks` $\rightarrow$ USD, `sing dollar` $\rightarrow$ SGD, `yen` $\rightarrow$ JPY, `quid` $\rightarrow$ GBP).
  - Defaults amount to `1` if missing (e.g. `USD to EUR`).
  - Defaults base to `USD` if missing (e.g. `to MYR`).
  - Multi-currency targets in a single query (e.g. `Convert 100 USD to MYR, SGD, and JPY`).
- **Live Real-Time Rates with Offline Fallback**:
  - Primary rate sources: Open Exchange Rates and European Central Bank (Frankfurter API).
  - Automatic local cache (`.currency_rates_cache.json`) with disclaimer timestamps when offline.
- **Strict, Clear Output Structure**:
  - Result Statement, Exchange Rate Summary, and Quick Insights (inverse rate and rounded estimations).
- **Multiple Interfaces**:
  - One-shot CLI query mode
  - Interactive REPL console
  - Zero-dependency local Web Dashboard

---

## Quick Start

### 1. One-Shot Command Mode
Run any currency query directly from your terminal:

```bash
# Multi-target query
uv run python main.py "100 USD to MYR, SGD, and JPY"

# Shorthand & slang
uv run python main.py "50 rm to bucks"

# Symbols
uv run python main.py "$250 to yen"

# Default amount & base
uv run python main.py "to MYR"
```

### 2. Interactive Terminal REPL
Launch the interactive session:

```bash
uv run python main.py
```

```text
CurrencyBot> 100 USD to MYR
Result Statement:
100.00 USD = 406.47 MYR

Exchange Rate Summary:
• Rate: 1 USD = 4.0647 MYR
• Last Updated: Thu, 05 Nov 2026 00:02:31 +0000

Quick Insights:
• Inverse: 1 MYR = 0.2460 USD
• Rounded: 100 USD is approximately 406 MYR.
```

### 3. Web Dashboard
Launch the web interface:

```bash
uv run python main.py --web
```
Open [http://localhost:8000](http://localhost:8000) in your browser.

---

## Running Tests
Run the automated test suite with pytest:

```bash
uv run pytest
```

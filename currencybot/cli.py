"""
Command-line interface for CurrencyBot.
Supports both single-shot query execution and interactive REPL mode.
"""

import sys
import argparse

# Ensure standard UTF-8 encoding on Windows console
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from currencybot.converter import CurrencyConverter

BANNER = """
=============================================================
              CurrencyBot - Currency Converter
=============================================================
Commands & Examples:
  • 100 USD to MYR, SGD, and JPY
  • 50 rm to bucks
  • EUR to USD
  • to MYR
  • Type 'exit' or 'quit' to close.
-------------------------------------------------------------
"""


def run_interactive(converter: CurrencyConverter):
    """Runs the interactive REPL loop."""
    print(BANNER)
    while True:
        try:
            query = input("\nCurrencyBot> ").strip()
            if not query:
                continue
            if query.lower() in ("exit", "quit", "q"):
                print("Goodbye!")
                break
            
            output = converter.process_query(query)
            print()
            print(output)
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")


def main():
    parser = argparse.ArgumentParser(description="CurrencyBot - Fast and accurate currency converter.")
    parser.add_argument(
        "query",
        nargs="*",
        help="Currency conversion query (e.g. '100 rm to usd', 'USD to MYR, SGD, JPY')",
    )
    parser.add_argument(
        "--web",
        action="store_true",
        help="Launch the local web dashboard server",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port for the web server (default: 8000)",
    )

    args = parser.parse_args()

    if args.web:
        from currencybot.web_server import run_server
        run_server(port=args.port)
        return

    converter = CurrencyConverter()

    if args.query:
        # One-shot mode
        full_query = " ".join(args.query)
        output = converter.process_query(full_query)
        print(output)
    else:
        # Interactive mode
        run_interactive(converter)


if __name__ == "__main__":
    main()

"""
Zero-dependency lightweight HTTP server and REST API for CurrencyBot Web Interface.
"""

import http.server
import json
import urllib.parse
from pathlib import Path
from currencybot.converter import CurrencyConverter
from currencybot.rates_service import RatesService

STATIC_DIR = Path(__file__).parent.parent / "static"


class CurrencyBotRequestHandler(http.server.SimpleHTTPRequestHandler):
    converter = CurrencyConverter()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(STATIC_DIR), **kwargs)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        
        # API: /api/convert?q=...
        if parsed.path == "/api/convert":
            params = urllib.parse.parse_qs(parsed.query)
            query = params.get("q", [""])[0]
            output_text = self.converter.process_query(query)
            response_data = {
                "success": "Clarification needed" not in output_text and "Unable to retrieve" not in output_text,
                "query": query,
                "formatted_output": output_text,
            }
            self._send_json(response_data)
            return

        # API: /api/rates
        if parsed.path == "/api/rates":
            rates, updated, is_cached, disclaimer = self.converter.rates_service.get_all_usd_rates()
            # Return all available rates for the table
            response_data = {
                "base": "USD",
                "rates": rates,
                "last_updated": updated,
                "is_cached": is_cached,
                "disclaimer": disclaimer,
            }
            self._send_json(response_data)
            return

        # Serve static assets
        super().do_GET()

    def _send_json(self, data: dict, status: int = 200):
        body = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        # Concise logging
        pass


def run_server(port: int = 8000):
    server_address = ("", port)
    httpd = http.server.HTTPServer(server_address, CurrencyBotRequestHandler)
    print(f"\n=============================================================")
    print(f" CurrencyBot Web Dashboard running at: http://localhost:{port}")
    print(f" Press Ctrl+C to stop.")
    print(f"=============================================================\n")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server...")
        httpd.server_close()

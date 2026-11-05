"""
Vercel serverless function: /api/rates
"""

from http.server import BaseHTTPRequestHandler
import json
import urllib.request


def fetch_rates() -> dict:
    try:
        req = urllib.request.Request("https://open.er-api.com/v6/latest/USD",
                                     headers={"User-Agent": "CurrencyBot/1.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data.get("result") == "success":
                rates = data["rates"]
                rates["USD"] = 1.0
                return {
                    "base": "USD",
                    "rates": rates,
                    "last_updated": data.get("time_last_update_utc", "Unknown"),
                    "is_cached": False,
                    "disclaimer": None,
                }
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
                return {
                    "base": "USD",
                    "rates": rates,
                    "last_updated": data.get("date", "Unknown"),
                    "is_cached": False,
                    "disclaimer": None,
                }
    except Exception:
        pass

    return {
        "base": "USD",
        "rates": {},
        "last_updated": "Unavailable",
        "is_cached": True,
        "disclaimer": "Could not fetch live rates.",
    }


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        result = fetch_rates()
        body = json.dumps(result, indent=2).encode("utf-8")

        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

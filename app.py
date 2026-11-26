"""SlayGuard X — server HTTP stdlib. Run: python3 app.py (port 8765).

Baru di OKX Build X (vs SlayGuard asli):
- chain xlayer (mainnet 196) + xlayer-testnet (1952)
- GET /api/tapeout — status on-chain TapeOut (factory/market) read-only
- GET /api/circuit — netlist + bukti verifikasi Risk Circuit NAND
"""
import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from analyzer import analyze, gas_price_gwei, tapeout_status
from llm import explain

ROOT = Path(__file__).parent
STATIC = ROOT / "static"
sys.path.insert(0, str(ROOT / "circuit"))
from risk_circuit import netlist_json  # noqa: E402


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):  # senyap
        pass

    def _send(self, code, body, ctype="application/json"):
        raw = body.encode() if isinstance(body, str) else body
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self._send(200, (STATIC / "index.html").read_bytes(), "text/html")
        elif self.path == "/health":
            self._send(200, json.dumps({"ok": True}))
        elif self.path == "/api/circuit":
            self._send(200, json.dumps(netlist_json()))
        elif self.path.startswith("/api/tapeout"):
            chain = "xlayer"
            if "testnet" in self.path:
                chain = "xlayer-testnet"
            try:
                self._send(200, json.dumps(tapeout_status(chain)))
            except Exception as e:  # noqa: BLE001
                self._send(500, json.dumps({"error": str(e)}))
        elif self.path.startswith("/api/gasprice"):
            chain = "xlayer"
            if "testnet" in self.path:
                chain = "xlayer-testnet"
            try:
                self._send(200, json.dumps(
                    {"chain": chain, "gas_price_gwei": gas_price_gwei(chain)}))
            except Exception as e:  # noqa: BLE001
                self._send(500, json.dumps({"error": str(e)}))
        else:
            self._send(404, json.dumps({"error": "not found"}))

    def do_POST(self):
        if self.path != "/api/audit":
            self._send(404, json.dumps({"error": "not found"}))
            return
        try:
            n = int(self.headers.get("Content-Length") or 0)
            payload = json.loads(self.rfile.read(n) or b"{}")
            address = (payload.get("address") or "").strip()
            chain = (payload.get("chain") or "bsc").strip().lower()
            result = analyze(address, chain)
            text, mode = explain(result)
            result["explanation"] = text
            result["explanation_mode"] = mode
            self._send(200, json.dumps(result))
        except ValueError as e:
            self._send(400, json.dumps({"error": str(e)}))
        except Exception as e:  # noqa: BLE001
            self._send(500, json.dumps({"error": f"audit gagal: {type(e).__name__}: {e}"}))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8765"))
    srv = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"SlayGuard AI jalan di http://127.0.0.1:{port}")
    srv.serve_forever()

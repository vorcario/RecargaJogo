"""Local-only browser diagnostics for the original layout mock."""

from __future__ import annotations

import json
from http import HTTPStatus
from http.server import ThreadingHTTPServer

from local_layout_server_v4 import ROOT
from local_layout_server_v5 import StableLayoutHandler


DIAGNOSTIC_SCRIPT = """
<script>
(() => {
  const report = (kind, value) => {
    const payload = JSON.stringify({kind, message: String(value && (value.message || value.reason || value)), stack: value && value.error && value.error.stack || ''});
    fetch('/api/client-error', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: payload}).catch(() => {});
  };
  window.addEventListener('error', event => report('error', event));
  window.addEventListener('unhandledrejection', event => report('rejection', event));
})();
</script>
"""


class DiagnosticLayoutHandler(StableLayoutHandler):
    def do_GET(self) -> None:
        if self._request_path() not in ("/", "/index.html"):
            super().do_GET()
            return
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        body = html.replace("</head>", DIAGNOSTIC_SCRIPT + "</head>").encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:
        if self._request_path() == "/api/client-error":
            length = int(self.headers.get("Content-Length", "0"))
            payload = self.rfile.read(length).decode("utf-8", errors="replace")
            print("BROWSER_DIAGNOSTIC", payload, flush=True)
            self._send_json({})
            return
        super().do_POST()


if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", 8080), DiagnosticLayoutHandler).serve_forever()

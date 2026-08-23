"""Prints local UI error reports to diagnose the static demonstration safely."""

from http.server import ThreadingHTTPServer

from local_layout_server_v6 import DiagnosticLayoutHandler


class ErrorLogHandler(DiagnosticLayoutHandler):
    def do_POST(self) -> None:
        if self._request_path() == "/api/log":
            length = int(self.headers.get("Content-Length", "0"))
            payload = self.rfile.read(length).decode("utf-8", errors="replace")
            print("LOCAL_UI_LOG", payload, flush=True)
            self._send_json({})
            return
        super().do_POST()


if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", 8080), ErrorLogHandler).serve_forever()

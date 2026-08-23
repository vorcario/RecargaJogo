"""Host the captured single-page layout on every internal route without backend access."""

from __future__ import annotations

from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parent
ASSET_CDN = "https://assets.recargajogo.com.br/gop/mshop/www/live/assets/"


class LayoutOnlyHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def _request_path(self) -> str:
        return unquote(urlsplit(self.path).path).lstrip("/")

    def _serve_spa_route(self) -> bool:
        request_path = self._request_path()
        if not request_path or "." in Path(request_path).name:
            return False
        if not (ROOT / request_path).exists():
            self.path = "/index.html"
            return True
        return False

    def do_GET(self) -> None:
        request_path = self._request_path()
        local_path = ROOT / request_path
        if request_path.startswith("js/") and not local_path.is_file():
            self.send_response(302)
            self.send_header("Location", ASSET_CDN + request_path.removeprefix("js/"))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            return
        self._serve_spa_route()
        super().do_GET()

    def do_HEAD(self) -> None:
        self._serve_spa_route()
        super().do_HEAD()

    def end_headers(self) -> None:
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://assets.recargajogo.com.br; "
            "style-src 'self' 'unsafe-inline' https://assets.recargajogo.com.br; "
            "img-src 'self' data: https://assets.recargajogo.com.br "
            "https://contentgarena-a.akamaihd.net https://cdn-gop.garenanow.com; "
            "font-src 'self' data: https://assets.recargajogo.com.br; "
            "connect-src 'none'; frame-src 'none'; object-src 'none'; "
            "base-uri 'self'; form-action 'none'",
        )
        self.send_header("Cache-Control", "no-store")
        super().end_headers()


if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", 8080), LayoutOnlyHandler).serve_forever()

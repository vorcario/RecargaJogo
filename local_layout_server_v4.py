"""Serve the original SPA with local mock data and no real backend connection."""

from __future__ import annotations

import json
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parent
ASSET_CDN = "https://assets.recargajogo.com.br/gop/mshop/www/live/assets/"
MOCK_APPS = {
    "apps": [
        {
            "app_id": 900001,
            "app_code": "demo-arena",
            "app_name": "Arena de Demonstração",
            "name": "Arena de Demonstração",
            "visibility": True,
            "mshop_order": 1,
            "priority": 1,
        },
        {
            "app_id": 900002,
            "app_code": "demo-racing",
            "app_name": "Corrida de Demonstração",
            "name": "Corrida de Demonstração",
            "visibility": True,
            "mshop_order": 2,
            "priority": 2,
        },
        {
            "app_id": 900003,
            "app_code": "demo-kingdom",
            "app_name": "Reino de Demonstração",
            "name": "Reino de Demonstração",
            "visibility": True,
            "mshop_order": 3,
            "priority": 3,
        },
    ]
}
MOCK_ROUTES = {
    "/api/shop/apps": MOCK_APPS,
    "/api/shop/banners": {"banners": []},
    "/api/shop/billboard": {"billboard": None, "billboards": []},
}


class LayoutOnlyHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def _request_path(self) -> str:
        return urlsplit(self.path).path

    def _send_json(self, data: object) -> None:
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _serve_spa_route(self) -> None:
        request_path = unquote(self._request_path()).lstrip("/")
        if request_path and "." not in Path(request_path).name and not (ROOT / request_path).exists():
            self.path = "/index.html"

    def do_GET(self) -> None:
        request_path = self._request_path()
        if request_path in MOCK_ROUTES:
            self._send_json(MOCK_ROUTES[request_path])
            return
        if request_path.startswith("/api/"):
            self._send_json({})
            return
        local_path = ROOT / unquote(request_path).lstrip("/")
        if request_path.startswith("/js/") and not local_path.is_file():
            self.send_response(HTTPStatus.FOUND)
            self.send_header("Location", ASSET_CDN + request_path.removeprefix("/js/"))
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
            "connect-src 'self'; frame-src 'none'; object-src 'none'; "
            "base-uri 'self'; form-action 'none'",
        )
        self.send_header("Cache-Control", "no-store")
        super().end_headers()


if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", 8080), LayoutOnlyHandler).serve_forever()

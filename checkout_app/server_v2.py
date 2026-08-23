"""Servidor v2: referência visual sem checkout fixo e checkout independente."""

from __future__ import annotations

from http import HTTPStatus

from .catalog_store import public_catalog
from .server import CATEGORY_PAGES, CheckoutHandler

ROOT_SCRIPT_V2 = """
<link rel="stylesheet" href="/css/integrated-categories.css">
<link rel="stylesheet" href="/css/reference-enhancements.css">
<script defer src="/js/reference-state.js"></script>
<script defer src="/js/integrated-categories.js"></script>
<script defer src="/js/reference-page-v2.js"></script>
"""
CHILD_SCRIPT_V2 = """
<link rel="stylesheet" href="/css/category-diamond-image.css">
<link rel="stylesheet" href="/css/reference-enhancements.css">
<script src="/js/reference-selection.js"></script>
<script src="/js/reference-enhancements.js"></script>
"""


class CheckoutHandlerV2(CheckoutHandler):
    def _serve_reference_root(self) -> None:
        from local_layout_server_v4 import ROOT
        from local_layout_server_v6 import DIAGNOSTIC_SCRIPT
        from local_layout_server_v9 import PAYMENT_GUARD

        html = (ROOT / "index.html").read_text(encoding="utf-8")
        html = html.replace(
            'src="js/002.js"',
            'src="https://assets.recargajogo.com.br/gop/mshop/www/live/assets/index-d5acf6c3.js"',
        )
        body = html.replace("</head>", DIAGNOSTIC_SCRIPT + PAYMENT_GUARD + ROOT_SCRIPT_V2 + "</head>").encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _serve_category_page(self, request_path: str) -> None:
        from local_layout_server_v4 import ROOT

        html = (ROOT / request_path.lstrip("/")).read_text(encoding="utf-8")
        body = html.replace("</body>", CHILD_SCRIPT_V2 + "</body>").encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        request_path = self._request_path()
        if request_path in {"/checkout", "/checkout/"} or request_path.startswith("/checkout/pix/"):
            from local_layout_server_v4 import ROOT

            self._serve_file(ROOT / "checkout_v2.html", "text/html; charset=utf-8")
            return
        if request_path == "/api/catalog":
            self._send_json({"products": public_catalog()})
            return
        if request_path in {"/", "/index.html"}:
            self._serve_reference_root()
            return
        if request_path in CATEGORY_PAGES:
            self._serve_category_page(request_path)
            return
        super().do_GET()

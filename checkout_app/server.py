"""HTTP local: checkout próprio e ponte segura com a página de referência."""

from __future__ import annotations

import json
import time
from collections import defaultdict, deque
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse

from local_layout_server_v4 import ROOT
from local_layout_server_v6 import DIAGNOSTIC_SCRIPT
from local_layout_server_v9 import PAYMENT_GUARD
from local_layout_server_v12 import FrameEnabledLocalArtworkHandler

from .errors import CheckoutError, ValidationError

ROOT_SCRIPT = """
<link rel="stylesheet" href="/css/integrated-categories.css">
<link rel="stylesheet" href="/css/reference-checkout-bridge.css">
<script defer src="/js/integrated-categories.js"></script>
<script defer src="/js/reference-checkout-bridge.js"></script>
"""
CHILD_SCRIPT = """
<link rel="stylesheet" href="/css/category-diamond-image.css">
<script src="/js/reference-selection.js"></script>
"""
CATEGORY_PAGES = {"/categoria_1_local.html", "/categoria_2_local.html", "/categoria_3_local.html"}


class RateLimiter:
    def __init__(self, maximum: int = 30, window_seconds: int = 60) -> None:
        self.maximum = maximum
        self.window_seconds = window_seconds
        self.buckets: dict[str, deque[float]] = defaultdict(deque)

    def allowed(self, client: str) -> bool:
        now = time.monotonic()
        bucket = self.buckets[client]
        while bucket and bucket[0] <= now - self.window_seconds:
            bucket.popleft()
        if len(bucket) >= self.maximum:
            return False
        bucket.append(now)
        return True


class CheckoutHandler(FrameEnabledLocalArtworkHandler):
    service = None
    limiter = RateLimiter()

    def _request_path(self) -> str:
        return urlparse(self.path).path

    def _send_json(self, value: dict, status: int = HTTPStatus.OK) -> None:
        body = json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_error_json(self, error: CheckoutError) -> None:
        self._send_json({"error": {"code": error.code, "message": error.message}}, error.status_code)

    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0 or length > 16_384:
            raise ValidationError("Corpo da solicitação inválido.")
        try:
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ValidationError("JSON inválido.") from error
        if not isinstance(payload, dict):
            raise ValidationError("JSON inválido.")
        return payload

    def _read_raw(self) -> bytes:
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0 or length > 65_536:
            raise ValidationError("Webhook inválido.")
        return self.rfile.read(length)

    def _serve_file(self, path: Path, content_type: str) -> None:
        body = path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _serve_reference_root(self) -> None:
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        html = html.replace(
            'src="js/002.js"',
            'src="https://assets.recargajogo.com.br/gop/mshop/www/live/assets/index-d5acf6c3.js"',
        )
        additions = DIAGNOSTIC_SCRIPT + PAYMENT_GUARD + ROOT_SCRIPT
        body = html.replace("</head>", additions + "</head>").encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _serve_category_page(self, request_path: str) -> None:
        html = (ROOT / request_path.lstrip("/")).read_text(encoding="utf-8")
        body = html.replace("</body>", CHILD_SCRIPT + "</body>").encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _allowed(self) -> bool:
        return self.limiter.allowed(self.client_address[0])

    def do_GET(self) -> None:
        request_path = self._request_path()
        try:
            if request_path in {"/checkout", "/checkout/"} or request_path.startswith("/checkout/pix/"):
                self._serve_file(ROOT / "checkout.html", "text/html; charset=utf-8")
                return
            if request_path.startswith("/api/orders/"):
                if not self._allowed():
                    self._send_json({"error": {"code": "RATE_LIMITED", "message": "Tente novamente em instantes."}}, HTTPStatus.TOO_MANY_REQUESTS)
                    return
                order_id = request_path.removeprefix("/api/orders/")
                order = self.service.get_order(order_id, self.headers.get("X-Checkout-Token", ""))
                self._send_json(order)
                return
            if request_path == "/api/bot/fulfillment/next":
                self.service.assert_bot_token(self.headers.get("Authorization"))
                self._send_json({"events": self.service.bot_events()})
                return
            if request_path in {"/", "/index.html"}:
                self._serve_reference_root()
                return
            if request_path in CATEGORY_PAGES:
                self._serve_category_page(request_path)
                return
            super().do_GET()
        except CheckoutError as error:
            self._send_error_json(error)

    def do_POST(self) -> None:
        request_path = self._request_path()
        try:
            if request_path == "/api/orders":
                if not self._allowed():
                    self._send_json({"error": {"code": "RATE_LIMITED", "message": "Tente novamente em instantes."}}, HTTPStatus.TOO_MANY_REQUESTS)
                    return
                payload = self._read_json()
                order, token, created = self.service.create_order(payload, self.headers.get("Idempotency-Key", ""))
                self._send_json({"order": order, "checkoutToken": token, "created": created}, HTTPStatus.CREATED if created else HTTPStatus.OK)
                return
            if request_path.startswith("/api/orders/") and request_path.endswith("/pix"):
                if not self._allowed():
                    self._send_json({"error": {"code": "RATE_LIMITED", "message": "Tente novamente em instantes."}}, HTTPStatus.TOO_MANY_REQUESTS)
                    return
                order_id = request_path.removeprefix("/api/orders/").removesuffix("/pix").rstrip("/")
                order = self.service.create_pix(
                    order_id, self.headers.get("X-Checkout-Token", ""), self.headers.get("Idempotency-Key", "")
                )
                self._send_json(order, HTTPStatus.CREATED)
                return
            if request_path == "/api/webhooks/turbofy":
                raw = self._read_raw()
                result = self.service.handle_turbofy_webhook(raw, self.headers.get("turbofy-signature"))
                self._send_json(result)
                return
            if request_path.startswith("/api/bot/orders/") and request_path.endswith("/status"):
                self.service.assert_bot_token(self.headers.get("Authorization"))
                order_id = request_path.removeprefix("/api/bot/orders/").removesuffix("/status").rstrip("/")
                payload = self._read_json()
                self._send_json(self.service.update_bot_status(order_id, str(payload.get("status", ""))))
                return
            super().do_POST()
        except CheckoutError as error:
            self._send_error_json(error)

    def log_message(self, format: str, *args) -> None:
        # Não registra corpo de pedido, playerId, códigos PIX ou dados de autenticação.
        super().log_message(format, *args)

    def end_headers(self) -> None:
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://assets.recargajogo.com.br; "
            "style-src 'self' 'unsafe-inline' https://assets.recargajogo.com.br; "
            "img-src 'self' data: https://assets.recargajogo.com.br https://contentgarena-a.akamaihd.net https://cdn-gop.garenanow.com; "
            "font-src 'self' data: https://assets.recargajogo.com.br; connect-src 'self'; "
            "frame-src 'self'; object-src 'none'; base-uri 'self'; form-action 'none'",
        )
        self.send_header("Cache-Control", "no-store")
        SimpleHTTPRequestHandler.end_headers(self)

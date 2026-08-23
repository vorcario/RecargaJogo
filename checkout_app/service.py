"""Regras de negócio: catálogo, pedidos, PIX, webhook e fila do bot."""

from __future__ import annotations

import hashlib
import hmac
import json
import re
import secrets
import threading
from typing import Any

from .catalog import get_product
from .config import Settings
from .errors import AuthorizationError, ValidationError
from .repository import OrderRepository
from .turbofy import TurbofyClient

PLAYER_ID_RE = re.compile(r"^[0-9]{4,32}$")
IDEMPOTENCY_RE = re.compile(r"^[A-Za-z0-9._:-]{16,200}$")


class CheckoutService:
    def __init__(self, settings: Settings, repository: OrderRepository, turbofy: TurbofyClient) -> None:
        self.settings = settings
        self.repository = repository
        self.turbofy = turbofy
        self._pix_locks: dict[str, threading.Lock] = {}
        self._pix_locks_guard = threading.Lock()

    def _token_hash(self, token: str) -> str:
        return hmac.new(self.settings.app_secret.encode("utf-8"), token.encode("utf-8"), hashlib.sha256).hexdigest()

    def _assert_token(self, order: dict[str, Any], token: str) -> None:
        if not token or not hmac.compare_digest(order["checkout_token_hash"], self._token_hash(token)):
            raise AuthorizationError("Acesso ao pedido não autorizado.")

    @staticmethod
    def _assert_idempotency_key(key: str) -> None:
        if not IDEMPOTENCY_RE.fullmatch(key or ""):
            raise ValidationError("Chave de idempotência inválida.")

    @staticmethod
    def _mask_player(player_id: str) -> str:
        if len(player_id) <= 4:
            return "•" * len(player_id)
        return "•" * (len(player_id) - 4) + player_id[-4:]

    @staticmethod
    def _request_hash(player_id: str, product_id: str, method: str) -> str:
        return hashlib.sha256(f"{player_id}|{product_id}|{method}".encode()).hexdigest()

    def create_order(self, payload: dict[str, Any], idempotency_key: str) -> tuple[dict[str, Any], str, bool]:
        self._assert_idempotency_key(idempotency_key)
        player_id = str(payload.get("playerId", "")).strip()
        product_id = str(payload.get("productId", "")).strip()
        method = str(payload.get("paymentMethod", "PIX")).upper()
        if not PLAYER_ID_RE.fullmatch(player_id):
            raise ValidationError("Informe um ID de jogador válido.")
        product = get_product(product_id)
        if not product:
            raise ValidationError("Produto inválido.")
        if method != "PIX":
            raise ValidationError("Somente PIX está disponível neste checkout.")

        token = secrets.token_urlsafe(32)
        order_id = f"ord_{secrets.token_urlsafe(18)}"
        order, created = self.repository.create_order(
            order_id=order_id,
            checkout_token_hash=self._token_hash(token),
            player_id=player_id,
            product=product,
            idempotency_key=idempotency_key,
            request_hash=self._request_hash(player_id, product_id, method),
        )
        # Em replay idempotente o token original não é reapresentado: o navegador já o possui em sessionStorage.
        return self.public_order(order), token if created else "", created

    def _pix_lock(self, order_id: str) -> threading.Lock:
        with self._pix_locks_guard:
            return self._pix_locks.setdefault(order_id, threading.Lock())

    def create_pix(self, order_id: str, checkout_token: str, idempotency_key: str) -> dict[str, Any]:
        self._assert_idempotency_key(idempotency_key)
        order = self.repository.get_order(order_id)
        self._assert_token(order, checkout_token)
        if order["payment_status"] != "PENDING":
            return self.public_order(order, include_pix=True)
        with self._pix_lock(order_id):
            order = self.repository.get_order(order_id)
            if not order["provider_payment_id"]:
                charge = self.turbofy.create_pix_charge(order)
                order = self.repository.store_pix_charge(order_id, charge)
            return self.public_order(order, include_pix=True)

    def get_order(self, order_id: str, checkout_token: str, include_pix: bool = True) -> dict[str, Any]:
        order = self.repository.get_order(order_id)
        self._assert_token(order, checkout_token)
        return self.public_order(order, include_pix=include_pix)

    def public_order(self, order: dict[str, Any], include_pix: bool = False) -> dict[str, Any]:
        result: dict[str, Any] = {
            "id": order["id"],
            "playerIdMasked": self._mask_player(order["player_id"]),
            "product": {
                "id": order["product_id"],
                "baseDiamonds": order["base_diamonds"],
                "bonusDiamonds": order["bonus_diamonds"],
                "totalDiamonds": order["total_diamonds"],
            },
            "amountCents": order["amount_cents"],
            "paymentMethod": order["payment_method"],
            "paymentStatus": order["payment_status"],
            "fulfillmentStatus": order["fulfillment_status"],
            "status": order["status"],
            "createdAt": order["created_at"],
        }
        if include_pix and order.get("pix_copy_paste"):
            result["pix"] = {
                "qrCode": order["pix_qr_code"],
                "copyPaste": order["pix_copy_paste"],
                "expiresAt": order["pix_expires_at"],
                "beneficiaryName": order["beneficiary_name"],
            }
        return result

    def handle_turbofy_webhook(self, raw_body: bytes, signature: str | None) -> dict[str, Any]:
        self.turbofy.verify_webhook(raw_body, signature)
        try:
            payload = json.loads(raw_body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ValidationError("Webhook inválido.") from error
        if not isinstance(payload, dict):
            raise ValidationError("Webhook inválido.")
        event_type = str(payload.get("event") or payload.get("type") or payload.get("eventType") or "")
        data = payload.get("data") if isinstance(payload.get("data"), dict) else payload
        charge = data.get("charge") if isinstance(data.get("charge"), dict) else data
        external_ref = str(charge.get("externalRef") or data.get("externalRef") or "") or None
        provider_id = str(charge.get("id") or data.get("id") or "") or None
        event_id = str(payload.get("eventId") or payload.get("id") or "")
        if not event_id:
            event_id = hashlib.sha256(raw_body).hexdigest()
        payload_hash = hashlib.sha256(raw_body).hexdigest()
        order, processed, fulfillment_created = self.repository.record_webhook_and_apply(
            event_id=event_id,
            event_type=event_type,
            payload_hash=payload_hash,
            order_id=external_ref,
            provider_payment_id=provider_id,
        )
        return {"processed": processed, "fulfillmentCreated": fulfillment_created, "orderId": order["id"] if order else None}

    def bot_events(self) -> list[dict[str, Any]]:
        events = []
        for order in self.repository.ready_fulfillment_events():
            events.append({
                "event": "order.ready_for_fulfillment",
                "orderId": order["id"],
                "playerId": order["player_id"],
                "productId": order["product_id"],
                "baseDiamonds": order["base_diamonds"],
                "bonusDiamonds": order["bonus_diamonds"],
                "totalDiamonds": order["total_diamonds"],
                "paymentStatus": order["payment_status"],
            })
        return events

    def update_bot_status(self, order_id: str, status: str) -> dict[str, Any]:
        return self.public_order(self.repository.set_fulfillment_status(order_id, status))

    def assert_bot_token(self, authorization: str | None) -> None:
        expected = self.settings.bot_api_token
        token = authorization.removeprefix("Bearer ").strip() if authorization else ""
        if not expected or not token or not hmac.compare_digest(expected, token):
            raise AuthorizationError("Token do bot inválido.")

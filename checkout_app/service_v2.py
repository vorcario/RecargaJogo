"""Serviço atual usando o catálogo comercial centralizado."""

from __future__ import annotations

import secrets
from typing import Any

from .catalog_store import get_product
from .errors import ValidationError
from .service import PLAYER_ID_RE, CheckoutService


class CheckoutServiceV2(CheckoutService):
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
        return self.public_order(order), token if created else "", created

"""Cliente HTTP da TurbofyPay: executado somente no backend."""

from __future__ import annotations

import hashlib
import hmac
import json
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .config import Settings
from .errors import AuthorizationError, GatewayConfigurationError, GatewayError


class TurbofyClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def _credentials(self) -> dict[str, str]:
        if not self.settings.turbofy_client_id or not self.settings.turbofy_client_secret:
            raise GatewayConfigurationError("Pagamento indisponível no momento.")
        return {
            "x-client-id": self.settings.turbofy_client_id,
            "x-client-secret": self.settings.turbofy_client_secret,
        }

    def create_pix_charge(self, order: dict[str, Any]) -> dict[str, Any]:
        expires_at = (datetime.now(timezone.utc) + timedelta(minutes=15)).isoformat(timespec="seconds")
        payload: dict[str, Any] = {
            "amountCents": int(order["amount_cents"]),
            "description": f"Pedido {order['id']} — Nebula Checkout",
            "externalRef": order["id"],
            "expiresAt": expires_at,
            "metadata": {"orderId": order["id"], "productId": order["product_id"]},
        }
        if self.settings.turbofy_webhook_url:
            payload["webhook_url"] = self.settings.turbofy_webhook_url
        body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        headers = {
            **self._credentials(),
            "Content-Type": "application/json",
            "x-idempotency-key": order["provider_idempotency_key"],
        }
        request = Request(f"{self.settings.turbofy_api_base}/sellers/pix", data=body, headers=headers, method="POST")
        try:
            with urlopen(request, timeout=15) as response:
                data = json.loads(response.read().decode("utf-8"))
        except HTTPError as error:
            # A resposta detalhada do gateway pode conter campos internos; não é retornada ao navegador.
            raise GatewayError("Não foi possível emitir o PIX no momento.") from error
        except (URLError, TimeoutError, json.JSONDecodeError) as error:
            raise GatewayError("Não foi possível emitir o PIX no momento.") from error

        pix = data.get("pix") if isinstance(data, dict) else None
        if not isinstance(data, dict) or not data.get("id") or not isinstance(pix, dict) or not pix.get("copyPaste"):
            raise GatewayError("O gateway não retornou os dados necessários do PIX.")
        return data

    def verify_webhook(self, raw_body: bytes, signature: str | None) -> None:
        if not self.settings.turbofy_webhook_secret:
            raise AuthorizationError("Webhook não configurado.")
        if not signature:
            raise AuthorizationError("Assinatura do webhook ausente.")
        expected = hmac.new(
            self.settings.turbofy_webhook_secret.encode("utf-8"), raw_body, hashlib.sha256
        ).hexdigest()
        provided = signature.removeprefix("sha256=").strip()
        if not hmac.compare_digest(expected, provided):
            raise AuthorizationError("Assinatura do webhook inválida.")

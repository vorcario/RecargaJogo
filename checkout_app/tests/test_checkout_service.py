from __future__ import annotations

import hashlib
import hmac
import json
import tempfile
import unittest
from pathlib import Path

from checkout_app.config import Settings
from checkout_app.errors import ValidationError
from checkout_app.repository import OrderRepository
from checkout_app.service import CheckoutService


class FakeTurbofy:
    def __init__(self, webhook_secret: str) -> None:
        self.webhook_secret = webhook_secret
        self.created = 0

    def create_pix_charge(self, order):
        self.created += 1
        return {
            "id": f"pix_{order['id']}",
            "status": "PENDING",
            "pix": {
                "qrCode": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAAB",
                "copyPaste": f"PIX-{order['id']}",
                "expiresAt": "2030-01-01T00:00:00+00:00",
            },
            "beneficiary": {"name": "Nebula Checkout"},
        }

    def verify_webhook(self, raw_body: bytes, signature: str | None) -> None:
        expected = hmac.new(self.webhook_secret.encode(), raw_body, hashlib.sha256).hexdigest()
        if not signature or not hmac.compare_digest(signature.removeprefix("sha256="), expected):
            raise AssertionError("assinatura de teste inválida")


class CheckoutServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        secret = "test-webhook-secret"
        self.settings = Settings(
            database_path=Path(self.tempdir.name) / "checkout.sqlite3",
            app_secret="test-app-secret",
            bot_api_token="bot-test-token",
            turbofy_api_base="https://api.turbofypay.com",
            turbofy_client_id="test-id",
            turbofy_client_secret="test-secret",
            turbofy_webhook_secret=secret,
            turbofy_webhook_url="https://example.test/api/webhooks/turbofy",
            environment="test",
        )
        self.repository = OrderRepository(self.settings.database_path)
        self.gateway = FakeTurbofy(secret)
        self.service = CheckoutService(self.settings, self.repository, self.gateway)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def create_order(self, key: str = "order-idempotency-key-0001"):
        return self.service.create_order(
            {"playerId": "123456789", "productId": "diamonds_520", "paymentMethod": "PIX", "amountCents": 1},
            key,
        )

    def signed_webhook(self, event: str, order_id: str, event_id: str) -> tuple[bytes, str]:
        payload = {"event": event, "eventId": event_id, "data": {"id": f"pix_{order_id}", "externalRef": order_id}}
        raw = json.dumps(payload, separators=(",", ":")).encode()
        signature = "sha256=" + hmac.new(self.settings.turbofy_webhook_secret.encode(), raw, hashlib.sha256).hexdigest()
        return raw, signature

    def test_price_is_taken_from_server_catalog_not_browser(self) -> None:
        order, _, _ = self.create_order()
        self.assertEqual(order["amountCents"], 2099)
        self.assertEqual(order["product"]["baseDiamonds"], 520)
        self.assertEqual(order["product"]["bonusDiamonds"], 104)

    def test_invalid_product_and_missing_player_are_rejected(self) -> None:
        with self.assertRaises(ValidationError):
            self.service.create_order({"playerId": "123456789", "productId": "other", "paymentMethod": "PIX"}, "invalid-product-key-0001")
        with self.assertRaises(ValidationError):
            self.service.create_order({"productId": "diamonds_520", "paymentMethod": "PIX"}, "missing-player-key-001")

    def test_pending_order_does_not_create_fulfillment(self) -> None:
        order, _, _ = self.create_order()
        self.assertEqual(order["paymentStatus"], "PENDING")
        self.assertEqual(self.service.bot_events(), [])
        self.assertEqual(self.repository.fulfillment_event_count(order["id"]), 0)

    def test_duplicate_webhook_does_not_duplicate_fulfillment(self) -> None:
        order, _, _ = self.create_order()
        raw, signature = self.signed_webhook("charge.paid", order["id"], "evt_paid_1")
        first = self.service.handle_turbofy_webhook(raw, signature)
        duplicate = self.service.handle_turbofy_webhook(raw, signature)
        self.assertTrue(first["fulfillmentCreated"])
        self.assertFalse(duplicate["processed"])
        self.assertEqual(self.repository.fulfillment_event_count(order["id"]), 1)

    def test_paid_generates_one_event_even_when_paid_event_repeats_with_new_id(self) -> None:
        order, _, _ = self.create_order()
        for event_id in ("evt_paid_a", "evt_paid_b"):
            raw, signature = self.signed_webhook("charge.paid", order["id"], event_id)
            self.service.handle_turbofy_webhook(raw, signature)
        events = self.service.bot_events()
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["event"], "order.ready_for_fulfillment")
        self.assertEqual(events[0]["paymentStatus"], "PAID")

    def test_expired_charge_becomes_expired(self) -> None:
        order, _, _ = self.create_order()
        raw, signature = self.signed_webhook("charge.expired", order["id"], "evt_expired_1")
        self.service.handle_turbofy_webhook(raw, signature)
        stored = self.repository.get_order(order["id"])
        self.assertEqual(stored["payment_status"], "EXPIRED")
        self.assertEqual(stored["status"], "EXPIRED")

    def test_double_idempotent_order_and_pix_creation_create_one_charge(self) -> None:
        first, token, created = self.create_order("same-idempotency-key-0001")
        second, replay_token, replay_created = self.create_order("same-idempotency-key-0001")
        self.assertTrue(created)
        self.assertFalse(replay_created)
        self.assertEqual(first["id"], second["id"])
        self.assertEqual(replay_token, "")
        pix_one = self.service.create_pix(first["id"], token, "pix-idempotency-key-00001")
        pix_two = self.service.create_pix(first["id"], token, "pix-idempotency-key-00001")
        self.assertEqual(self.gateway.created, 1)
        self.assertEqual(pix_one["pix"]["copyPaste"], pix_two["pix"]["copyPaste"])

    def test_secrets_are_absent_from_frontend_bundle(self) -> None:
        root = Path(__file__).resolve().parents[2]
        public_content = (root / "checkout.html").read_text() + (root / "js" / "checkout.js").read_text()
        self.assertNotIn("TURBOFY_CLIENT_SECRET", public_content)
        self.assertNotIn("TURBOFY_CLIENT_ID", public_content)
        self.assertNotIn("x-client-secret", public_content.lower())


if __name__ == "__main__":
    unittest.main()

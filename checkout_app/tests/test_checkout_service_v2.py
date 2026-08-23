from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from checkout_app.config import Settings
from checkout_app.repository import OrderRepository
from checkout_app.service_v2 import CheckoutServiceV2


class _Gateway:
    pass


class CheckoutServiceV2Tests(unittest.TestCase):
    def test_price_remains_server_controlled_in_new_catalog(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            settings = Settings(
                database_path=Path(temporary) / "checkout.sqlite3", app_secret="a", bot_api_token="b",
                turbofy_api_base="https://api.turbofypay.com", turbofy_client_id="", turbofy_client_secret="",
                turbofy_webhook_secret="", turbofy_webhook_url="", environment="test",
            )
            service = CheckoutServiceV2(settings, OrderRepository(settings.database_path), _Gateway())
            order, _, _ = service.create_order(
                {"playerId": "123456789", "productId": "diamonds_65", "paymentMethod": "PIX", "amountCents": 1},
                "order-v2-price-protection-0001",
            )
        self.assertEqual(order["amountCents"], 499)
        self.assertEqual(order["product"]["baseDiamonds"], 65)


if __name__ == "__main__":
    unittest.main()

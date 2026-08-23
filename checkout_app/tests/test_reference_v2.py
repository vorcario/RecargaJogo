from __future__ import annotations

import unittest
from pathlib import Path

from checkout_app.catalog_store import get_product


class ReferenceV2Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parents[2]

    def test_first_three_displayed_prices_come_from_central_catalog(self) -> None:
        self.assertEqual(get_product("diamonds_65").amount_cents, 499)
        self.assertEqual(get_product("diamonds_100").amount_cents, 599)
        self.assertEqual(get_product("diamonds_310").amount_cents, 1700)

    def test_new_reference_bridge_has_no_demo_or_nebula_fixed_handoff(self) -> None:
        source = (self.root / "checkout_app" / "server_v2.py").read_text()
        self.assertNotIn("reference-checkout-bridge", source)
        self.assertNotIn("modo demonstração", source.lower())

    def test_new_frontend_bundle_has_no_gateway_secrets(self) -> None:
        public = "".join(
            (self.root / path).read_text()
            for path in (
                "checkout_v2.html",
                "js/checkout-v2.js",
                "js/reference-page-v2.js",
                "js/reference-enhancements.js",
            )
        ).lower()
        self.assertNotIn("turbofy_client_secret", public)
        self.assertNotIn("turbofy_client_id", public)
        self.assertNotIn("x-client-secret", public)

    def test_checkout_client_posts_identifiers_without_a_price(self) -> None:
        source = (self.root / "js" / "reference-page-v2.js").read_text()
        self.assertIn("playerId: safeId(), productId: state.selectedProductId, paymentMethod: 'PIX'", source)
        self.assertNotIn("amountCents:", source)


if __name__ == "__main__":
    unittest.main()

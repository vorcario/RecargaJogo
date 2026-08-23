from __future__ import annotations

import unittest

from checkout_app.catalog_store import get_product


class CatalogStoreTests(unittest.TestCase):
    def test_explicit_front_catalog_prices(self) -> None:
        self.assertEqual(get_product("diamonds_65").amount_cents, 499)
        self.assertEqual(get_product("diamonds_100").amount_cents, 599)
        self.assertEqual(get_product("diamonds_310").amount_cents, 1700)


if __name__ == "__main__":
    unittest.main()

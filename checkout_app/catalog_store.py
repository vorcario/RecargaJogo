"""Fonte única de produtos usada por API, checkout e preço exibido."""

from __future__ import annotations

from .catalog import Product

PRODUCTS: dict[str, Product] = {
    "diamonds_65": Product("diamonds_65", 65, 0, 499),
    "diamonds_100": Product("diamonds_100", 100, 0, 599),
    "diamonds_310": Product("diamonds_310", 310, 0, 1700),
    "diamonds_520": Product("diamonds_520", 520, 104, 2099),
    "diamonds_1060": Product("diamonds_1060", 1060, 106, 4499),
    "diamonds_2180": Product("diamonds_2180", 2180, 218, 8799),
    "diamonds_5600": Product("diamonds_5600", 5600, 560, 20999),
    "diamonds_22400": Product("diamonds_22400", 22400, 2240, 83999),
}


def get_product(product_id: str) -> Product | None:
    return PRODUCTS.get(product_id)


def public_catalog() -> list[dict[str, int | str]]:
    return [
        {
            "id": product.id,
            "baseDiamonds": product.base_diamonds,
            "bonusDiamonds": product.bonus_diamonds,
            "totalDiamonds": product.total_diamonds,
            "amountCents": product.amount_cents,
        }
        for product in PRODUCTS.values()
    ]

"""Catálogo confiável: valores jamais vêm do navegador."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Product:
    id: str
    base_diamonds: int
    bonus_diamonds: int
    amount_cents: int

    @property
    def total_diamonds(self) -> int:
        return self.base_diamonds + self.bonus_diamonds


PRODUCTS: dict[str, Product] = {
    "diamonds_65": Product("diamonds_65", 65, 0, 449),
    "diamonds_100": Product("diamonds_100", 100, 10, 699),
    "diamonds_310": Product("diamonds_310", 310, 31, 1399),
    "diamonds_520": Product("diamonds_520", 520, 104, 2099),
    "diamonds_1060": Product("diamonds_1060", 1060, 106, 4499),
    "diamonds_2180": Product("diamonds_2180", 2180, 218, 8799),
    "diamonds_5600": Product("diamonds_5600", 5600, 560, 20999),
    "diamonds_22400": Product("diamonds_22400", 22400, 2240, 83999),
}


def get_product(product_id: str) -> Product | None:
    return PRODUCTS.get(product_id)

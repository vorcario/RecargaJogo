"""Executa a referência visual e o Nebula Checkout próprio na mesma origem local."""

from __future__ import annotations

from http.server import ThreadingHTTPServer

from checkout_app.config import Settings
from checkout_app.repository import OrderRepository
from checkout_app.server import CheckoutHandler
from checkout_app.service import CheckoutService
from checkout_app.turbofy import TurbofyClient

if __name__ == "__main__":
    settings = Settings.from_env()
    settings.assert_production_ready()
    repository = OrderRepository(settings.database_path)
    CheckoutHandler.service = CheckoutService(settings, repository, TurbofyClient(settings))
    print("Referência visual: http://0.0.0.0:8080/")
    print("Checkout próprio:  http://0.0.0.0:8080/checkout")
    ThreadingHTTPServer(("0.0.0.0", 8080), CheckoutHandler).serve_forever()

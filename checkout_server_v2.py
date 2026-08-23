"""Executa a referência visual corrigida e o checkout independente em rede local."""

from __future__ import annotations

from http.server import ThreadingHTTPServer

from checkout_app.config import Settings
from checkout_app.repository import OrderRepository
from checkout_app.server_v2 import CheckoutHandlerV2
from checkout_app.service_v2 import CheckoutServiceV2
from checkout_app.turbofy import TurbofyClient

if __name__ == "__main__":
    settings = Settings.from_env()
    settings.assert_production_ready()
    repository = OrderRepository(settings.database_path)
    CheckoutHandlerV2.service = CheckoutServiceV2(settings, repository, TurbofyClient(settings))
    print("Referência local: http://0.0.0.0:8080  |  Checkout independente: /checkout")
    ThreadingHTTPServer(("0.0.0.0", 8080), CheckoutHandlerV2).serve_forever()

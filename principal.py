"""Ponto de entrada da interface local principal."""

from http.server import ThreadingHTTPServer

from local_layout_server_v14 import DiamondArtworkHandler


if __name__ == "__main__":
    print("Interface local principal em http://0.0.0.0:8080/")
    ThreadingHTTPServer(("0.0.0.0", 8080), DiamondArtworkHandler).serve_forever()

"""Ponto de entrada principal da interface local integrada."""

from http.server import ThreadingHTTPServer

from local_layout_server_v13 import CategoryContentHandler


if __name__ == "__main__":
    print("Interface local principal em http://0.0.0.0:8080/")
    ThreadingHTTPServer(("0.0.0.0", 8080), CategoryContentHandler).serve_forever()

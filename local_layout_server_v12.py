"""Integrated local sections; permits only the same-origin local iframe."""

from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

from local_layout_server_v11 import ExtendedLocalArtworkHandler


class FrameEnabledLocalArtworkHandler(ExtendedLocalArtworkHandler):
    def end_headers(self) -> None:
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://assets.recargajogo.com.br; "
            "style-src 'self' 'unsafe-inline' https://assets.recargajogo.com.br; "
            "img-src 'self' data: https://assets.recargajogo.com.br "
            "https://contentgarena-a.akamaihd.net https://cdn-gop.garenanow.com; "
            "font-src 'self' data: https://assets.recargajogo.com.br; "
            "connect-src 'self'; frame-src 'self'; object-src 'none'; "
            "base-uri 'self'; form-action 'none'",
        )
        self.send_header("Cache-Control", "no-store")
        SimpleHTTPRequestHandler.end_headers(self)


if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", 8080), FrameEnabledLocalArtworkHandler).serve_forever()

"""Serve the latest local carousel artwork using its native wide aspect ratio."""

from http.server import ThreadingHTTPServer

from local_layout_server_v9 import LocalArtworkHandler


UPDATED_BANNERS = {
    "banners": [
        {
            "content_id": "pacote-de-nivel",
            "image": "/img/01_pacote_de_nivel.png",
            "url": "",
            "extra": {},
        },
        {
            "content_id": "passe-booyah",
            "image": "/img/02_passe_booyah.png",
            "url": "",
            "extra": {},
        },
        {
            "content_id": "centro-de-recarga",
            "image": "/img/03_centro_de_recarga.png",
            "url": "",
            "extra": {},
        },
    ]
}


class UpdatedArtworkHandler(LocalArtworkHandler):
    def do_GET(self) -> None:
        if self._request_path() == "/api/shop/banners":
            self._send_json(UPDATED_BANNERS)
            return
        super().do_GET()


if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", 8080), UpdatedArtworkHandler).serve_forever()

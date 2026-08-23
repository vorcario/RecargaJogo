"""Adds stable empty channel and logging responses to the local layout mock."""

from http.server import ThreadingHTTPServer

from local_layout_server_v4 import LayoutOnlyHandler


EMPTY_CHANNELS = {
    "channels": [],
    "tabs": [],
    "announcements": [],
    "announcement_ids_by_position": {},
}


class StableLayoutHandler(LayoutOnlyHandler):
    def do_GET(self) -> None:
        if self._request_path().startswith("/api/shop/apps/channels"):
            self._send_json(EMPTY_CHANNELS)
            return
        super().do_GET()

    def do_POST(self) -> None:
        # Tracking and form-like requests are acknowledged locally and discarded.
        self._send_json({})


if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", 8080), StableLayoutHandler).serve_forever()

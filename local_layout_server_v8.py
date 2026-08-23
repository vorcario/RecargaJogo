"""Use one coherent public UI module graph while keeping all data local and mocked."""

from __future__ import annotations

from http import HTTPStatus
from http.server import ThreadingHTTPServer

from local_layout_server_v4 import ASSET_CDN, MOCK_APPS, ROOT
from local_layout_server_v6 import DIAGNOSTIC_SCRIPT
from local_layout_server_v7 import ErrorLogHandler


COHERENT_ENTRY = ASSET_CDN + "index-d5acf6c3.js"
MOCK_APPS_WITH_PLATFORMS = {
    "apps": [
        {**app, "platforms": ["garena", "facebook", "vk"]}
        for app in MOCK_APPS["apps"]
    ]
}


class CoherentLayoutHandler(ErrorLogHandler):
    def do_GET(self) -> None:
        request_path = self._request_path()
        if request_path == "/api/shop/apps":
            self._send_json(MOCK_APPS_WITH_PLATFORMS)
            return
        if request_path not in ("/", "/index.html"):
            super().do_GET()
            return
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        html = html.replace('src="js/002.js"', f'src="{COHERENT_ENTRY}"')
        body = html.replace("</head>", DIAGNOSTIC_SCRIPT + "</head>").encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", 8080), CoherentLayoutHandler).serve_forever()

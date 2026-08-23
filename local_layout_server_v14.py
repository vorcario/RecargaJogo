"""Principal local with the supplied diamond artwork in categories."""

from http import HTTPStatus
from http.server import ThreadingHTTPServer

from local_layout_server_v4 import ROOT
from local_layout_server_v13 import CategoryContentHandler


POINT_STYLESHEET = '<link rel="stylesheet" href="/css/category-diamond-image.css">'
CATEGORY_PAGES = {"/categoria_1_local.html", "/categoria_2_local.html", "/categoria_3_local.html"}


class DiamondArtworkHandler(CategoryContentHandler):
    def do_GET(self) -> None:
        request_path = self._request_path()
        if request_path not in CATEGORY_PAGES:
            super().do_GET()
            return

        page = ROOT / request_path.lstrip("/")
        html = page.read_text(encoding="utf-8")
        body = html.replace("</head>", POINT_STYLESHEET + "</head>").encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", 8080), DiamondArtworkHandler).serve_forever()

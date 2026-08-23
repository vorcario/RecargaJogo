"""Original carousel layout with local content inserted into steps 1, 2 and 3."""

from http import HTTPStatus
from http.server import ThreadingHTTPServer

from local_layout_server_v4 import ROOT
from local_layout_server_v6 import DIAGNOSTIC_SCRIPT
from local_layout_server_v9 import PAYMENT_GUARD
from local_layout_server_v12 import FrameEnabledLocalArtworkHandler


STEP_CONTENT = """
<link rel="stylesheet" href="/css/integrated-categories.css">
<script defer src="/js/integrated-categories.js"></script>
"""


class CategoryContentHandler(FrameEnabledLocalArtworkHandler):
    def do_GET(self) -> None:
        if self._request_path() not in {"/", "/index.html"}:
            super().do_GET()
            return

        html = (ROOT / "index.html").read_text(encoding="utf-8")
        html = html.replace(
            'src="js/002.js"',
            'src="https://assets.recargajogo.com.br/gop/mshop/www/live/assets/index-d5acf6c3.js"',
        )
        additions = DIAGNOSTIC_SCRIPT + PAYMENT_GUARD + STEP_CONTENT
        body = html.replace("</head>", additions + "</head>").encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", 8080), CategoryContentHandler).serve_forever()

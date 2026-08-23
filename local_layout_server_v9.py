"""Original UI with local carousel artwork and payment navigation disabled."""

from __future__ import annotations

from http import HTTPStatus
from http.server import ThreadingHTTPServer

from local_layout_server_v4 import ROOT
from local_layout_server_v6 import DIAGNOSTIC_SCRIPT
from local_layout_server_v8 import CoherentLayoutHandler


LOCAL_CATALOG = {
    "apps": [
        {
            "app_id": 100067,
            "app_code": "freefire",
            "app_name": "Free Fire",
            "name": "Free Fire",
            "icon": "/img/006.ico",
            "platforms": ["garena", "facebook", "vk"],
            "visibility": True,
            "mshop_order": 1,
            "priority": 1,
        }
    ]
}
LOCAL_BANNERS = {
    "banners": [
        {
            "content_id": "freefire-centro-recarga",
            "image": "/img/freefire_centro_recarga_20_bonus.png",
            "url": "",
            "extra": {},
        },
        {
            "content_id": "freefire-pacote-nivel",
            "image": "/img/freefire_pacote_nivel_18_desconto.png",
            "url": "",
            "extra": {},
        },
        {
            "content_id": "freefire-passe-booyah",
            "image": "/img/freefire_passe_booyah.png",
            "url": "",
            "extra": {},
        },
    ]
}
PAYMENT_GUARD = """
<script>
(() => {
  const blocked = /\\/(?:buy|payment|pending|result|sms|fastspring)(?:\\/|$|\\?)/i;
  const prevent = event => {
    const link = event.target.closest && event.target.closest('a[href]');
    if (link && blocked.test(link.getAttribute('href'))) {
      event.preventDefault();
      event.stopImmediatePropagation();
    }
  };
  document.addEventListener('click', prevent, true);
  for (const method of ['pushState', 'replaceState']) {
    const original = history[method].bind(history);
    history[method] = function(state, title, url) {
      if (url && blocked.test(String(url))) return;
      return original(state, title, url);
    };
  }
})();
</script>
"""


class LocalArtworkHandler(CoherentLayoutHandler):
    def do_GET(self) -> None:
        request_path = self._request_path()
        if request_path == "/api/shop/apps":
            self._send_json(LOCAL_CATALOG)
            return
        if request_path == "/api/shop/banners":
            self._send_json(LOCAL_BANNERS)
            return
        if request_path not in ("/", "/index.html"):
            super().do_GET()
            return
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        html = html.replace('src="js/002.js"', 'src="https://assets.recargajogo.com.br/gop/mshop/www/live/assets/index-d5acf6c3.js"')
        body = html.replace("</head>", DIAGNOSTIC_SCRIPT + PAYMENT_GUARD + "</head>").encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", 8080), LocalArtworkHandler).serve_forever()

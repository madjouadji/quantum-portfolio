"""Build the site, then preview it exactly as GitHub Pages will serve it: under /quantum-portfolio/.

    python3 serve.py              # http://localhost:8000/quantum-portfolio/
    python3 serve.py --port 8080
    python3 serve.py --no-build   # serve the existing site/ folder

Like GitHub Pages, missing paths return site/404.html with status 404.
"""
from __future__ import annotations

import argparse
import tomllib
import webbrowser
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SITE = ROOT / "site"
with open(ROOT / "content" / "site.toml", "rb") as f:
    BASE = tomllib.load(f)["base_path"].rstrip("/")  # "/quantum-portfolio"


class SubpathHandler(SimpleHTTPRequestHandler):
    def send_head(self):
        path = self.path.split("?", 1)[0].split("#", 1)[0]
        if path in ("/", "", BASE):  # like GitHub Pages: /quantum-portfolio -> /quantum-portfolio/
            self.send_response(302)
            self.send_header("Location", BASE + "/")
            self.end_headers()
            return None
        if path != BASE and not path.startswith(BASE + "/"):
            return self.not_found()
        self.path = self.path[len(BASE):] or "/"
        target = Path(self.translate_path(self.path))
        if target.is_dir():
            target = target / "index.html"
        if not target.exists():
            return self.not_found()
        return super().send_head()

    def not_found(self):
        body = (SITE / "404.html").read_bytes()
        self.send_response(404)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
        return None

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--no-build", action="store_true")
    parser.add_argument("--no-open", action="store_true", help="do not open the browser")
    args = parser.parse_args()
    if not args.no_build:
        import build
        build.build()
    url = f"http://localhost:{args.port}{BASE}/"
    server = ThreadingHTTPServer(("127.0.0.1", args.port), partial(SubpathHandler, directory=str(SITE)))
    print(f"Preview: {url}   (Ctrl+C to stop)")
    if not args.no_open:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()

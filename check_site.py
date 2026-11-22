"""Check the generated site/ folder before publishing.

    python3 build.py && python3 check_site.py

Checks, for every HTML page:
  - internal links, stylesheets, scripts and images point to files that exist,
    resolved as if the site were served under /quantum-portfolio/;
  - links to #anchors point to an existing id;
  - one <h1>, a <title>, a meta description and a lang attribute;
  - no root-absolute link (starting with "/") outside the 404 page, since it would break under the subpath;
  - external links are listed, so they can be reviewed (only public pages should be linked).
Exit code 1 if a problem is found (used by the GitHub Actions workflow).
"""
from __future__ import annotations

import sys
import tomllib
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urljoin, urlparse

ROOT = Path(__file__).resolve().parent
SITE = ROOT / "site"
with open(ROOT / "content" / "site.toml", "rb") as f:
    BASE = tomllib.load(f)["base_path"]  # "/quantum-portfolio/"
HOST = "https://example.test"


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.refs, self.ids, self.h1, self.title, self.description, self.lang = [], set(), 0, False, False, False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a:
            self.ids.add(a["id"])
        if tag == "html" and a.get("lang"):
            self.lang = True
        if tag == "h1":
            self.h1 += 1
        if tag == "title":
            self.title = True
        if tag == "meta" and a.get("name") == "description" and a.get("content"):
            self.description = True
        for attr in ("href", "src"):
            if a.get(attr) and not (tag == "link" and a.get("rel") in ("canonical",)) and tag != "meta":
                self.refs.append((tag, a[attr]))


def main() -> int:
    if not SITE.exists():
        print("site/ not found: run python3 build.py first")
        return 1
    pages = sorted(SITE.rglob("*.html"))
    parsed = {}
    for page in pages:
        p = PageParser()
        p.feed(page.read_text(encoding="utf-8"))
        parsed[page] = p

    problems, external = [], set()
    for page, p in parsed.items():
        rel = page.relative_to(SITE).as_posix()
        page_url = HOST + BASE + rel
        if not p.lang:
            problems.append(f"{rel}: <html> has no lang attribute")
        if p.h1 != 1:
            problems.append(f"{rel}: {p.h1} <h1> elements (expected 1)")
        if not p.title or not p.description:
            problems.append(f"{rel}: missing <title> or meta description")
        for tag, ref in p.refs:
            if ref.startswith(("mailto:", "tel:")):
                continue
            if ref.startswith(("http://", "https://")):
                external.add(ref)
                continue
            if ref.startswith("/") and rel != "404.html":
                problems.append(f"{rel}: root-absolute link {ref!r} breaks under {BASE}")
            target = urlparse(urljoin(page_url, ref))
            if not target.path.startswith(BASE):
                problems.append(f"{rel}: {ref!r} leaves {BASE}")
                continue
            file = SITE / unquote(target.path[len(BASE):])
            if target.path.endswith("/"):
                file = file / "index.html"
            if not file.is_file():
                problems.append(f"{rel}: {ref!r} -> missing file {file.relative_to(SITE)}")
                continue
            if target.fragment and file.suffix == ".html":
                ids = parsed[file].ids if file in parsed else set()
                if target.fragment not in ids:
                    problems.append(f"{rel}: {ref!r} -> no element with id {target.fragment!r}")

    print(f"Checked {len(pages)} pages.")
    print("External links (review that each is public):")
    for url in sorted(external):
        print(f"  {url}")
    if problems:
        print(f"\n{len(problems)} problem(s):")
        for item in problems:
            print(f"  - {item}")
        return 1
    print("\nNo problems found.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

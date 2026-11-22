"""Build the static portfolio from content/*.toml and templates/ into site/.

    python3 build.py            # build
    python3 serve.py            # build, then preview at http://localhost:8000/quantum-portfolio/

Content lives in content/ (TOML), layout in templates/ (Jinja2), style and behaviour in static/.
Every page is written as its own HTML file with relative links, so the site works both under
https://madjouadji.github.io/quantum-portfolio/ and when opened from disk.
"""
from __future__ import annotations

import hashlib
import shutil
import sys
import tomllib
from datetime import date
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape

ROOT = Path(__file__).resolve().parent
CONTENT = ROOT / "content"
OUTPUT = ROOT / "site"
KNOWN_LANGUAGES = ("en", "fr")

# (page key, output file, template)
PAGES = (
    ("home", "index.html", "index.html"),
    ("about", "about.html", "about.html"),
    ("skills", "skills.html", "skills.html"),
    ("projects", "projects.html", "projects.html"),
    ("training", "training.html", "training.html"),
    ("contact", "contact.html", "contact.html"),
)

missing_translations: list[str] = []


def load(name: str) -> dict:
    with open(CONTENT / f"{name}.toml", "rb") as f:
        return tomllib.load(f)


def localize(value, lang: str, path: str = ""):
    """Pick the text for `lang`. English is the plain key; other languages use the suffix `_<lang>`.

    A missing translation falls back to English and is reported at the end of the build.
    """
    if isinstance(value, dict):
        suffixes = tuple(f"_{code}" for code in KNOWN_LANGUAGES if code != "en")
        result = {k: localize(v, lang, f"{path}.{k}") for k, v in value.items() if not k.endswith(suffixes)}
        if lang != "en":
            for key in list(result):
                translated = value.get(f"{key}_{lang}")
                if translated is not None:
                    result[key] = localize(translated, lang, f"{path}.{key}")
                elif isinstance(value[key], str):
                    missing_translations.append(f"{path}.{key}_{lang}".lstrip("."))
        return result
    if isinstance(value, list):
        return [localize(v, lang, f"{path}[{i}]") for i, v in enumerate(value)]
    return value


def validate(projects: list[dict], skills: dict, training: dict) -> None:
    """Refuse content that would overstate something (planned work with results, unknown links...)."""
    errors = []
    ids = {p["id"] for p in projects}
    if len(ids) != len(projects):
        errors.append("projects.toml: two projects share the same id")
    for p in projects:
        for field in ("id", "title", "status", "summary"):
            if not p.get(field):
                errors.append(f"projects.toml: project {p.get('id', '?')} has no {field}")
        if p.get("status") not in ("completed", "in_progress", "planned"):
            errors.append(f"projects.toml: {p['id']}: status must be completed, in_progress or planned")
        if p.get("status") == "planned":
            for field in ("verification", "results", "features", "github_url"):
                if p.get(field):
                    errors.append(f"projects.toml: planned project {p['id']} cannot have `{field}`")
        url = p.get("github_url")
        if url and not url.startswith("https://github.com/"):
            errors.append(f"projects.toml: {p['id']}: github_url must be a public https://github.com/ link")
    for category in skills["categories"]:
        for s in category["skills"]:
            if s["status"] not in skills["statuses"]:
                errors.append(f"skills.toml: {s['name']}: unknown status {s['status']!r}")
            if s["status"] == "demonstrated" and s.get("project") not in ids:
                errors.append(f"skills.toml: {s['name']}: 'demonstrated' needs `project` = an existing project id")
            if s.get("project") and s["project"] not in ids:
                errors.append(f"skills.toml: {s['name']}: unknown project {s['project']!r}")
    for course in training.get("courses", []):
        if course.get("project") and course["project"] not in ids:
            errors.append(f"training.toml: {course['code']}: unknown project {course['project']!r}")
    if errors:
        sys.exit("Content errors:\n  - " + "\n  - ".join(errors))


def asset_version() -> str:
    """Short hash of the static files: changes whenever they change, so browsers never keep stale CSS/JS."""
    digest = hashlib.sha1()
    for f in sorted((ROOT / "static").rglob("*")):
        if f.is_file():
            digest.update(f.read_bytes())
    return digest.hexdigest()[:10]


def build() -> None:
    site, ui_all = load("site"), load("ui")
    projects_raw, skills_raw, training_raw = load("projects")["projects"], load("skills"), load("training")
    validate(projects_raw, skills_raw, training_raw)

    languages = site["languages"]
    default = languages[0]
    base_url = site["site_url"].rstrip("/")
    version = asset_version()

    if OUTPUT.exists():
        shutil.rmtree(OUTPUT)  # always regenerated: never edit files in site/
    OUTPUT.mkdir()
    shutil.copytree(ROOT / "static", OUTPUT / "static")
    # Search-engine verification files (e.g. Google Search Console): copied to the site root.
    # Never delete them: Google checks them again from time to time.
    verification = ROOT / "verification"
    if verification.is_dir():
        for f in verification.iterdir():
            if f.is_file():
                shutil.copy2(f, OUTPUT / f.name)

    env = Environment(
        loader=FileSystemLoader(ROOT / "templates"),
        autoescape=select_autoescape(["html"]),
        undefined=StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
    )

    sitemap_urls = []
    for lang in languages:
        if lang not in ui_all:
            sys.exit(f"content/ui.toml has no [{lang}] table")
        folder = OUTPUT if lang == default else OUTPUT / lang
        folder.mkdir(exist_ok=True)
        lang_url = base_url + ("/" if lang == default else f"/{lang}/")
        data = localize({"site": site, "projects": projects_raw, "skills": skills_raw, "training": training_raw}, lang)
        projects = data["projects"]
        context = {
            "site": data["site"],
            "profile": data["site"]["profile"],
            "links": data["site"]["links"],
            "ui": ui_all[lang],
            "lang": lang,
            "pre": "" if lang == default else "../",  # path to static/
            "link_pre": "",  # page links stay inside the language folder
            "version": version,
            "year": date.today().year,
            "nav": [(key, out) for key, out, _ in PAGES],
            "projects": [p for p in projects if p["status"] != "planned"],
            "planned_projects": [p for p in projects if p["status"] == "planned"],
            "project_by_id": {p["id"]: p for p in projects},
            "skills": data["skills"],
            "training": data["training"],
        }
        for key, out, template in PAGES:
            url = lang_url + ("" if out == "index.html" else out)
            html = env.get_template(template).render(
                **context, page=key, meta=data["site"]["pages"][key], canonical=url, is_404=False
            )
            (folder / out).write_text(html, encoding="utf-8")
            sitemap_urls.append(url)

    # 404: GitHub Pages serves it for any missing path, at any depth, so it uses absolute links.
    lang = default
    data = localize({"site": site}, lang)
    html = env.get_template("404.html").render(
        site=data["site"], profile=data["site"]["profile"], links=data["site"]["links"], ui=ui_all[lang],
        lang=lang, pre=site["base_path"], link_pre=site["base_path"], version=version, year=date.today().year,
        nav=[(key, out) for key, out, _ in PAGES], page="notfound", meta=data["site"]["pages"]["notfound"],
        canonical=None, is_404=True,
    )
    (OUTPUT / "404.html").write_text(html, encoding="utf-8")

    today = date.today().isoformat()
    (OUTPUT / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "".join(f"  <url><loc>{u}</loc><lastmod>{today}</lastmod></url>\n" for u in sitemap_urls)
        + "</urlset>\n",
        encoding="utf-8",
    )
    (OUTPUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {base_url}/sitemap.xml\n", encoding="utf-8")
    (OUTPUT / ".nojekyll").touch()

    print(f"Built {len(sitemap_urls)} pages + 404.html into site/ ({', '.join(languages)})")
    for item in sorted(set(missing_translations)):
        print(f"  ! missing translation: {item}")


if __name__ == "__main__":
    build()

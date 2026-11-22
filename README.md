# Quantum portfolio — Adji Madjou

Professional portfolio focused on quantum computing training, programming projects and the path
towards quantum software development. Separate from the academic portfolio
(<https://madjouadji.github.io/portfolio/>).

Target address once published: <https://madjouadji.github.io/quantum-portfolio/>

## Why this architecture

A small **Python generator** (Jinja2 templates + TOML data files) produces plain static HTML.

- All editable content sits in four data files: a project is written once and appears everywhere it should
  (Home, Projects, Skills, Training).
- Each page is a real HTML file with **relative links**, so it works under the `/quantum-portfolio/` subpath,
  on direct access and on reload, with no client-side routing.
- No framework or paid service: one dependency (Jinja2), the same approach as the academic portfolio.
- Pages are readable without JavaScript. `main.js` adds the mobile menu, a discreet reveal effect and the
  animated quantum-circuit background (static when the visitor prefers reduced motion, paused in hidden tabs).

## Structure

```
content/                 ← EDIT HERE (text only)
  site.toml              profile, intro, career goal, About text, links, page titles/descriptions
  projects.toml          projects (completed, in progress, planned)
  skills.toml            skills by category, with honest statuses
  training.toml          IQuCode, courses, certifications
  ui.toml                interface labels (menu, headings), one table per language
templates/               page layouts (Jinja2): base.html + one template per page, macros.html
static/css/style.css     presentation (colours defined once at the top)
static/js/main.js        behaviour: mobile menu, reveal effect, animated circuit background
static/img/favicon.svg
build.py                 generates site/ (never edit site/ by hand)
serve.py                 local preview under /quantum-portfolio/, like GitHub Pages
check_site.py            checks links, assets, anchors and page structure
.github/workflows/pages.yml   build + check + deploy on every push to main
```

## Install and preview locally

```bash
cd ~/Documents/GitHub/quantum-portfolio
python3 -m venv .venv                      # once
.venv/bin/python -m pip install -r requirements.txt   # once
.venv/bin/python serve.py                  # builds, then opens http://localhost:8000/quantum-portfolio/
```

`Ctrl+C` stops the preview. Other commands:

```bash
.venv/bin/python build.py        # build only, into site/
.venv/bin/python check_site.py   # verify the built site (also run automatically on GitHub)
```

## Update the content

### Add a project (one file to edit)

1. Open `content/projects.toml` and copy an existing `[[projects]]` block.
2. Give it a new `id` (e.g. `quantum-teleportation-simulator`), a `title`, a `status`
   (`completed`, `in_progress` or `planned`), a `status_label` and a `summary`.
3. Fill in only the fields you can support with facts (context, contribution, features, verification,
   results...). Remove the others: empty sections are not displayed.
4. Add `github_url` **only** when the repository is public.
5. Run `.venv/bin/python serve.py` and check the result.

The build refuses inconsistent content, for example a planned project with results or tests,
a skill marked "Demonstrated in Project" without an existing project, or a non-public GitHub link format.

### Update a skill

In `content/skills.toml`, change its `status` and, for `demonstrated`, set `project` to the project id.
Statuses: `learning`, `practicing`, `demonstrated`, `research`, `background` (no percentages).

### Add a certification

In `content/training.toml`, add an entry to `certifications` only once it is obtained and its exact
title is confirmed. The Certifications section stays hidden while the list is empty.

### Change the BSQ712 status after the instructor's review

In `content/projects.toml` (project `bsq712-quantum-circuit-simulator`): update `status_label`,
`code_availability`, `code_note`, and add `github_url` once the repository is made public.
In `content/training.toml`, update the BSQ712 course `status`.

## Add French later

1. In `content/site.toml`, set `languages = ["en", "fr"]`.
2. In `content/ui.toml`, copy the `[en]` tables as `[fr]` and translate them.
3. In the content files, add a French version next to each text with the suffix `_fr`
   (e.g. `summary_fr = "..."`). Missing translations fall back to English and are listed by `build.py`.

French pages are then generated in `site/fr/`.

## Publish on GitHub Pages (not done yet)

1. **GitHub Desktop** → *File → Add Local Repository…* → choose `~/Documents/GitHub/quantum-portfolio`.
   If asked, choose *create a repository*.
2. Make the first commit (the `site/` and `.venv/` folders are ignored).
3. *Publish repository*: name **quantum-portfolio**, untick *Keep this code private*
   (GitHub Pages on a free account needs a public repository).
4. On GitHub: **Settings → Pages → Build and deployment → Source: GitHub Actions**.
5. Every push to `main` then runs `.github/workflows/pages.yml` (build, check, deploy).
   The site appears at <https://madjouadji.github.io/quantum-portfolio/> after the first successful run.
6. Optional: add the address to Google Search Console as a new *URL prefix* property and submit
   `sitemap.xml`.

## Content rules

- Career goal (Quantum Applications Scientist — Algorithms & Software, 2029) is shown as a goal, never as a position.
- The PhD is in pure mathematics; it is never presented as a quantum physics or quantum computing PhD.
- No invented publications, employers, collaborations, statistics or skill levels.
- The BSQ712 code is not copied into this site and not linked until it is public.
- Only contact details: institutional email, GitHub, academic portfolio. No form, no phone number.

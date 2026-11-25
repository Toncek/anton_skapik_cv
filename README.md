# Anton Škapík — Engineering CV & Indie Apps Showcase

Zero-build static site hosted on GitHub Pages (`master` branch) at `https://toncek.github.io/anton_skapik_cv/`.

## Site Structure

- `/` (`index.html`, `cv.pdf`) — Public software engineering & technical leadership CV, structured metadata (Open Graph, JSON-LD), print stylesheet, and downloadable PDF resume.
- `/apps/` (`apps/index.html`) — Public Indie Apps & Systems Showcase featuring mobile/desktop builds and closed-beta tester registration.
- `/journey/` (`journey/index.html`, `journey/stickers/index.html`) — Unlisted personal page & road sticker pack (`noindex, nofollow`, disallowed in `robots.txt`, excluded from `sitemap.xml`, and never linked from `/` or `/apps/`).
- `assets/apps/` — Optimized WebP showcase icons, banners, and mobile screenshots.
- `tests/` — Playwright verification suite (`tests/verify_site.py`); transient artifacts are written to `tests/.artifacts/` (gitignored).
- `docs/` — Repository audit and maintenance notes (`docs/AUDIT_REPORT.md`).

## Local Preview

Serve the repository over HTTP from the repo root (required for relative root paths and browser module/SVG behavior):

```bash
python3 -m http.server 8000
```

Then open `http://localhost:8000/` or `http://localhost:8000/apps/`.

## Verification

Run the Playwright verification suite before pushing:

```bash
python3 tests/verify_site.py
```

CI (`.github/workflows/ci.yml`) also validates required pages, `cv.pdf`, privacy boundaries (`robots.txt`, `sitemap.xml`, `noindex`, zero links to `/journey/`), and local `<img src>` resolution on `push` (`master`) and `pull_request`.

## Exporting `cv.pdf`

`cv.pdf` is generated directly from `index.html` using headless Chromium / Playwright PDF export with `@media print` styles enabled. Whenever `index.html` CV content changes, regenerate `cv.pdf` and verify it is present and non-empty at the repository root.

## Beta Tester Email Capture (`/apps/`)

The `/apps/` closed-beta sign-up form submits via `FormSubmit.co` targeting `Anton.skapik@gmail.com` (with an optional webhook constant in the page script for automated forwarding):

1. **First-time activation**: Submit the form once from the live GitHub Pages URL (or local preview) to trigger FormSubmit.co's confirmation email to `Anton.skapik@gmail.com`, and click the activation link inside that email before public launch.
2. **Optional webhook**: Set the optional webhook endpoint constant in `apps/index.html` if dual-dispatching sign-ups to a secondary backend or automation webhook.

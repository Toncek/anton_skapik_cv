# Repository Audit Report

Initial audit of `/home/toncek/work/projects/anton_skapik_cv` prior to remediation.

## Findings & Planned Remediations

| # | Area | Finding | Planned Remediation | Status |
|---|------|---------|---------------------|--------|
| 1 | `cv.pdf` | `index.html` links to `cv.pdf`, which was missing from the repository root (HTTP 404). | Generate and commit `cv.pdf` from `index.html` via headless Chromium `@media print` export; enforce existence & non-zero size in CI and `tests/verify_site.py`. | Planned |
| 2 | Stray Root Artifacts | ~2.4 MB of committed temporary verification files (`mobile_view.png`, `verification.png`, `server_output.log`, `view_images.html`, `playwright_test.py`, `verify_cuj.py`, `videos/cb2b3bb72a8ce3990a173b33c4dd25ba.webm`) including hardcoded `/app/` paths and screenshots. | Remove stray files with `git rm -f`, delete empty `videos/`, and ignore transient test outputs (`tests/.artifacts/`, `*.log`, etc.) in `.gitignore`. | Completed (Step 1) |
| 3 | Governance & Hosting Config | Missing `.gitignore`, `.nojekyll`, `AGENTS.md`, `GEMINI.md`, `CLAUDE.md`, `.antigravityrules`, `README.md`, and CI checks. | Add static GitHub Pages config (`.nojekyll`, `.gitignore`), shared Antigravity/Codex governance docs, `README.md`, and `.github/workflows/ci.yml`. | Completed (Step 1) |
| 4 | Privacy & SEO Boundaries | `/journey/index.html` lacked `<meta name="robots" content="noindex, nofollow">`, and root lacked `robots.txt` and `sitemap.xml` enforcing separation between public pages and `/journey/`. | Add `robots.txt` (`Disallow: /journey/`, `/tests/`, `/docs/`), `sitemap.xml` (only `/` and `/apps/`), `noindex, nofollow` on `/journey/`, and automated CI/Playwright checks ensuring zero cross-links from `/` or `/apps/` to `/journey/`. | In Progress (Step 1 / Step 2) |
| 5 | `/journey/` UX & Media | Portrait photos cropped faces and helmet; moon icon used a static SVG; Line ID lacked a copy-to-clipboard button. | Adjust `object-position` / framing on `/journey/` portraits so faces and helmet are preserved, replace static moon SVG with an improved visual/animated treatment, and add a one-click Line ID copy button. | Planned (Step 2) |
| 6 | `index.html` Completeness & Showcase | `index.html` lacked Open Graph tags, JSON-LD structured data, favicon, navigation to `/apps/`, `@media print` rules, GitHub profile link, peer tech stack details, and indie app showcase integration. | Add `favicon.svg`, OG/JSON-LD metadata, `@media print` layout, top nav linking `/` and `/apps/`, GitHub link, expanded tech stack, and create `/apps/` backed by optimized WebP assets in `assets/apps/`. | In Progress (Step 1 / Step 2) |

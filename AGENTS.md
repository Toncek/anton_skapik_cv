# AGENTS.md — Guidelines & Architecture for anton_skapik_cv

## Shared operating rules: Antigravity + Codex

`AGENTS.md` is the shared source of truth. Use Antigravity (`agy`) with the signed-in Google AI Pro account and Codex (`codex`) with the signed-in ChatGPT Plus account. Actively use both subscriptions for suitable work; neither is a permanent emergency-only fallback. Use official subscription authentication, never API keys, gateways, unofficial OAuth bridges, or paid API billing for normal work.

### Task ownership and provider allocation
- Select one owner per task. Antigravity/Gemini is preferred for broad analysis, specifications, architecture, feature decomposition, cross-cutting design, and complex reasoning. For Unity, prefer it for gameplay/system design, Burst/Jobs architecture, visual direction, and large feature planning.
- Codex is preferred for focused implementation, C#/Kotlin edits, refactoring, Editor/build tooling, tests, compile/debug loops, review, and verification. Codex can own complete features when appropriate. These are defaults, not strict restrictions or quality rankings.
- Use the other agent for independent review only when the task warrants spending the second plan's allowance. Do not start extra agents by default.

### Model preferences and quota
- User preferences, only when available in the current account selector: Antigravity Gemini 4 Argon (High) for complex work; Gemini 3.8 Flash for routine tasks. Codex GPT-6.1 Sol at medium/high reasoning for serious implementation/review; GPT-6 Luna for routine high-volume work; GPT-6 Astra sparingly for unusually hard work only if visible and available in Plus.
- Model names and access change. Check the live selector and account availability; never hard-code model IDs into scripts or assume access.
- Before long Antigravity jobs, check `/usage` (or `/quota` if supported) for both the five-hour refresh window and separate weekly limit. Keep AI Credit Overages at **Never**, and CLI `useG1Credits` false, unless the user explicitly authorizes spending.
- For Codex, check `/status` and the ChatGPT Codex usage dashboard for the model-dependent allowance and reset times; weekly limits may apply. Do not assume the same five-hour schedule as Antigravity.
- When a plan is low, give the next suitable new task to the other agent. Do not treat provider quota percentages as equivalent. Never restart a task on the other provider while the first may have modified files.

### Handoffs, safety, and verification
- Check `git status` before work and preserve unrelated user changes. Before switching agents, update `TASK_HANDOFF.md` or a structured task note with objective, source documents, decisions, modified files, current diff/state, tests/results, and remaining work.
- Never let two agents modify the same working tree concurrently. Independent parallel work requires separate Git worktrees and deliberate review/merge.
- Keep normal sandbox and approval protections. Do not default to unrestricted/yolo/bypass permissions. Always commit (staging only task-related files while preserving unrelated user changes) and push to the active remote branch when you finish work, after required verification passes (unless the user explicitly asks to keep changes uncommitted or a repository has no configured remote).
- Preserve project architecture, domain constraints, documentation hierarchy, build/test commands, and deprecated-design warnings. Run appropriate project checks and report exactly what ran and what did not. Do not run app builds for documentation-only changes without a project-specific reason.
- Read targeted sections and use `rg` for discovery. Keep responses concise; do not dump code or diffs unless requested.

---

## 1. Static Architecture & Deployment
- **Stack**: Zero-build static site using vanilla HTML5, CSS3, and ES6 JavaScript. No bundlers, Node runtime dependencies, or Jekyll processing (`.nojekyll` is present at root).
- **Hosting**: Deployed directly from the `master` branch to GitHub Pages (`https://toncek.github.io/anton_skapik_cv/`).
- **Directory Layout**:
  - `/` (`index.html`, `cv.pdf`, `favicon.svg`, `robots.txt`, `sitemap.xml`) — Public engineering CV and downloadable PDF.
  - `/apps/` (`apps/index.html`) — Public Indie Apps & Systems Showcase with closed-beta tester capture.
  - `/journey/` (`journey/index.html`, `journey/stickers/index.html`, local JPEG & vinyl sticker PNG assets) — Unlisted personal pages (`noindex, nofollow`).
  - `assets/apps/` — Optimized WebP showcase images (max quality 84, pre-sized for web).
  - `tests/` — Playwright end-to-end verification (`tests/verify_site.py`); transient outputs go to `tests/.artifacts/` (gitignored).
  - `docs/` — Repository audit and maintenance documentation (`docs/AUDIT_REPORT.md`).

---

## 2. 3-Tier `vega64-local` Routing
Follow the global 3-tier routing policy in `~/.gemini/config/rules/vega64-routing.md`:
- **Tier 1 (`vega64-local` MCP)**: Use `vega64_commit_message` for git diffs, `vega64_local_ask` for isolated utilities/boilerplate, and `vega64_generate_image` if new bespoke artwork is ever required (always review Tier 1 outputs before keeping).
- **Tier 2 (`flash` / `flash_lite` subagents)**: Delegate multi-file exploration, asset conversion scripts, and Playwright/CI test runs.
- **Tier 3 (Primary Frontier Model)**: Reserve for architecture, visual/UX design, privacy boundary reviews, and final verification.

---

## 3. Strict Privacy Boundary & Repository Visibility Rules
- **Route Separation**:
  - `/` is the public CV page.
  - `/apps/` is the public indie app showcase + closed-beta tester sign-up.
  - `/journey/` and `/journey/stickers/` are **private/unlisted personal pages**. Both MUST carry `<meta name="robots" content="noindex, nofollow">` (or `noindex, nofollow, noarchive`), MUST be disallowed in `robots.txt` (`Disallow: /journey/`), and MUST NEVER appear in `sitemap.xml`.
  - **No Cross-Linking**: `/` and `/apps/` MUST NEVER link to `/journey/` or `/journey/stickers/` (not in nav, footer, scripts, or JSON-LD).
- **Repository Visibility**:
  - Never link private GitHub repositories on public pages (`/` or `/apps/`). Only reference public repositories (e.g., `thai-cs-transcription`) or generic/store links where permitted.
- **No Stray Artifacts**:
  - Never commit screenshots, browser videos, server logs, or ad-hoc scratch scripts to the repository root. Use `tests/.artifacts/` (ignored by `.gitignore`).

---

## 4. Asset Budget (`assets/apps/*.webp`)
- Store all showcase screenshots, icons, and banners under `assets/apps/` as `.webp` (`quality=84`, preserving RGBA alpha for transparent icons/mascots).
- Respect dimension caps to keep total showcase payload lightweight (~1–2 MB total across all 16 assets):
  - App icons: max `256x256`
  - Mascots / portrait cards: max `384x384` (or max height `600` for tall character art)
  - Mobile screenshots: max width `480`
  - Desktop/feature banners & scenes: max width `800–960`
- All `<img>` tags must resolve to existing local files (or verified assets) and include descriptive `alt` text and `loading="lazy"` where below the fold.

---

## 5. Verification & `cv.pdf` Regeneration
- **Site Verification**: Run the Playwright suite before committing changes to HTML/CSS/JS/assets:
  ```bash
  python3 tests/verify_site.py
  ```
- **CI Parity Check**: `.github/workflows/ci.yml` runs on `push` (`master`), `pull_request`, and `workflow_dispatch` to validate required files (`index.html`, `apps/index.html`, `journey/index.html`, `journey/stickers/index.html`, 5 sticker PNGs, `cv.pdf`), `robots.txt` / `sitemap.xml` / `noindex` privacy boundaries, zero links to `journey` or `stickers` from public pages, and local `<img src>` resolution.
- **`cv.pdf` Regeneration**: Regenerate `cv.pdf` from `index.html` using headless Chromium / Playwright print-to-PDF with `@media print` styles enabled whenever `index.html` CV content changes, and verify `cv.pdf` exists and is non-empty before pushing.

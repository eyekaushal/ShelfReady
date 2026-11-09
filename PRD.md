# PRD — ShelfReady

> Product Requirement Document. Source of truth for *what* we build and *why*.
> Technical details live in `Design.md`; the step-by-step order lives in `plan.md`.

---

## 1. Problem

A shelf-recognition camera can only recognise products that are listed **correctly** in the product master (the catalog). Blurry reference photos, missing pack sizes, wrong barcodes, duplicates and look-alike variants (e.g. *Parle-G 100 g vs 250 g*) are a common cause of misclassification on the shelf.

**Analogy:** a kirana shop owner's smart camera can only recognise what's written properly in the product notebook. ShelfReady keeps that notebook clean.

## 2. Product vision

ShelfReady is a **recognition-ready SKU master**: a product catalog that sits *upstream* of a shelf-recognition system and keeps its reference data clean, searchable and easy to fill using AI.

Features are *inspired by publicly described challenges in retail image recognition*. We make no claims about Infilect's internal systems.

## 3. Users

| User | Needs |
|---|---|
| **Catalog manager** (logged in) | Add, edit and delete products quickly; fill forms from a pack photo; fix data-quality issues |
| **Viewer** (anonymous) | Browse, search and filter the catalog |
| **Staff / admin** | Edit or delete any product; resolve look-alikes |
| **Reviewer (Infilect)** | Clear demo, live URLs, Swagger, readable code |

## 4. Goals and non-goals

**Goals**
- Meet every base-spec item in the assignment, with no bugs.
- Use AI that is useful and safe: photo → form, natural-language search.
- Show domain understanding through the look-alike detector.

**Non-goals**
- Actual shelf image recognition.
- Payments, orders, carts (this is not a shop).
- Paid infrastructure, TypeScript, CLIP, Celery in production.

## 5. Functional requirements

### 5.1 Base spec (must be flawless)

| ID | Requirement |
|---|---|
| F1 | **Auth:** register, login (JWT), refresh, logout (blacklist), `GET /api/auth/me/` |
| F2 | **Product CRUD** with fields `name, brand, category, description, price, image_url` (+ optional `gtin, pack_size, variant, tags`) |
| F3 | **Search** across name, brand and description (case-insensitive) |
| F4 | **Filter** by brand, category (including sub-categories), min/max price |
| F5 | **Sort** by price, name, created_at (asc/desc) |
| F6 | **Pagination**: 12 per page, `page_size` param, max 100 |
| F7 | **Validation**: price > 0 (2 dp), http/https URL, length limits, valid GTIN; one consistent error format |
| F8 | **Permissions**: anyone can read; logged-in users can create; only the owner or staff can edit/delete |
| F9 | **Swagger / Redoc** at `/api/docs/` and `/api/redoc/` |
| F10 | **Structured logging** + request-id; every AI call logged (model, latency, tokens, status) |
| F11 | **Frontend**: login/register, list (search, filters, sort, pagination synced to the URL), details, add/edit form, delete modal, loading/empty/error states, toasts, responsive |
| F12 | **AI photo → form**: image URL or upload → Claude vision → prefilled form with an "AI-filled — please review" badge. Never auto-saves |
| F13 | **AI description generator**: name + brand + category → description + tags |
| F14 | **AI natural-language search**: sentence → whitelisted filters → removable chips → normal product list API. Falls back to keyword search |
| F15 | **Deployed**: Render (API) + Vercel (UI) + Neon (DB), with seed data and a demo account |

### 5.2 Add-ons

Only A1 was built. A2–A4 were dropped on 4 Nov 2026 for time.

| ID | Add-on | Why it matters for shelf recognition |
|---|---|---|
| A1 | **Look-alike SKU detector** (pHash + text embeddings) | Same-brand variants with near-identical packs are the hardest case for a camera |
| A2 | **Recognition-readiness score** (7 checks, dashboard) | Shows which products would hurt recognition, and what to fix first |
| A3 | **Smart bulk import** (AI column mapping, row validation, Celery) | Brands send messy spreadsheets; onboarding should be quick |
| A4 | **Change history** (optional) | New packaging means the recognition model must re-learn the SKU |

## 6. Non-functional requirements

- **Security:** secrets in env vars; SSRF-safe image fetching; packaging and spreadsheet text treated as untrusted data; AI endpoints throttled (20/hour per user).
- **Graceful degradation:** with no `ANTHROPIC_API_KEY`, the app still works and AI buttons show "AI unavailable".
- **Performance:** fits the Render free tier (512 MB). Cold start (~50 s) is mentioned in the README, kept awake by an UptimeRobot monitor.
- **Code quality:** OOP (one class per file in the backend), KISS, every line explainable in an interview.
- **Testing:** pytest for backend rules and permissions; Claude mocked in CI; frontend lint + build in CI.
- **Version control:** one branch per build block, merged into `main` via PRs with CI checks. `main` is always deployable, and the commit history shows clear, small steps for reviewers.

## 7. Success criteria

- [ ] All of F1–F15 work on the live URL in an incognito window.
- [ ] README has every section the brief requires.
- [ ] CI is green.
- [ ] Demo account and seed data are loaded in production.
- [ ] Submitted to Indira by **4 Nov 2026 night** (hard deadline: 5 Nov 2026, 9:00 AM IST).

## 8. Open questions

- ~~Cloudinary for permanent image uploads?~~ Decided in Block 7: yes, unsigned upload from the frontend (optional via env vars).

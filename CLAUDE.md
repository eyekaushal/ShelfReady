# CLAUDE.md — ShelfReady (Infilect Technical Assignment: Product Catalog + AI)

> **Project name:** ShelfReady. **GitHub repo:** `eyekaushal/shelfready`. Use "ShelfReady" in the UI header, page titles, README title and Swagger title.

> Read this whole file before writing any code. It is the single source of truth for this project.
> If something here conflicts with your own defaults, **this file wins**. If something is unclear, ask Kaushal before guessing.

---

## 0. Who / why / deadline

- **Candidate:** Kaushal (B.Tech CSE 2026). Strong in **MERN + JavaScript**, newer to Django. He must be able to **explain every line in a code walkthrough interview**. So: simple, readable code. No clever abstractions. Comments explain *why*, not *what*.
- **Company:** Infilect (Bangalore, founded 2018). Builds **retail shelf image recognition** for CPG/FMCG brands: photos of store shelves → which SKUs are present, facings, prices, share of shelf (product: InfiViz). Also builds agentic AI that processes documents/spreadsheets. Their own stack (from job posts): **Python, Django/DRF, PostgreSQL, React**.
- **Role:** Full Stack Development Intern. Recruiter contact: Indira Ashrit.
- **Assignment:** "Product Management & AI-Powered Search Platform". Full-stack app to manage and search a product catalog using **Django/DRF, React.js, PostgreSQL, REST APIs, GenAI**, deployed on public URLs.
- **Deadline:** **5 Nov 2026, 9:00 AM IST.** Target: everything deployed and submitted by **4 Nov night**. Timezone: IST.
- **Rule:** Build in the roadmap order (section 4). **Stop wherever the deadline hits.** A flawless base spec beats half-finished extras.

---

## 1. The story (use this in README + UI copy)

A shelf-recognition camera can only recognise products that are listed **correctly** in the product master (the catalog). Blurry reference photos, missing pack sizes, wrong barcodes, duplicates, and look-alike variants (e.g. *Parle-G 100 g vs 250 g*) are a common cause of misclassification on the shelf.

So this app is not a generic shop. It is a **SKU master / product catalog that is "recognition-ready"**: it sits *upstream* of a shelf-recognition system and keeps its reference data clean.

Simple analogy for README (Kaushal's wording style): a kirana shop owner's smart camera can only recognise what's written properly in his product notebook. This app keeps that notebook clean.

**Wording rules:**
- Say "a common cause of misclassification", never "guaranteed misclassification".
- Do **NOT** use the "70% of recognition errors come from master data" statistic. It could not be verified from Infilect's own pages.
- Don't claim to know Infilect's internal systems. Frame features as "inspired by publicly described challenges in retail image recognition".

---

## 2. Final decisions (already agreed — do not change without asking)

| Area | Decision |
|---|---|
| Backend | Python 3.12, Django 5.x, Django REST Framework |
| Auth | `djangorestframework-simplejwt` (access + refresh, refresh blacklist for logout) |
| DB | PostgreSQL. Production on **Neon** (free). Extensions: **pgvector**, **pg_trgm** |
| API docs | `drf-spectacular` → Swagger UI at `/api/docs/`, schema at `/api/schema/`, Redoc at `/api/redoc/` |
| Frontend | **React + Vite + plain JavaScript (NOT TypeScript)**. Kaushal must defend it in interview. |
| Frontend libs | React Router, TanStack Query, axios (interceptor for JWT refresh), Tailwind CSS |
| LLM | **Anthropic Claude API** (Kaushal has a key). Models via env vars (see section 9). Verify current model IDs in Anthropic docs before use. |
| Image similarity | **Perceptual hash (imagehash pHash)**. NOT CLIP (no free hosted API; too heavy for Render free 512 MB). |
| Text similarity | **Small local embedding model → pgvector**: `fastembed` with `BAAI/bge-small-en-v1.5` (384 dims, ONNX, no torch). Lazy-load. **Render uses the `pg_trgm` fallback** (`EMBEDDINGS_ENABLED=False`): the model peaks at ~320 MB on a 512 MB plan (measured in Block 10). Local Docker uses embeddings. The switch lives in `EmbeddingService`. |
| Hosting | Backend **Render** (free web service), frontend **Vercel**, DB **Neon** |
| Celery + Redis | **Local Docker Compose only** (no paid worker). In production set `CELERY_TASK_ALWAYS_EAGER=True` so the same task code runs inline. State this honestly in README. |
| Docker | `docker-compose.yml`: `db` (image `pgvector/pgvector:pg16`), `redis`, `backend`, `worker`, `frontend` |
| CI | GitHub Actions: ruff + pytest (Postgres service with pgvector image) + frontend lint + build. Runs on every push and on PRs into `main` |
| Git | One branch per block (`feature/...`), merged into `main` via PR. `main` is what gets deployed (section 16) |
| Not using | TypeScript, Gemini, OpenAI, CLIP, Celery in production, Google Cloud Run |

---

## 3. Base spec (required by the brief — must be flawless)

### Backend (Django + DRF)
- **Auth:** register, login (JWT pair), refresh, logout (blacklist refresh), `GET /api/auth/me/`.
- **Products CRUD:** create, retrieve, update (PUT/PATCH), delete.
- **Required product fields (from brief):** `name`, `brand`, `category`, `description`, `price`, `image_url`.
- **Search:** across name, brand, description (DRF `SearchFilter`, case-insensitive).
- **Filtering** (`django-filter`): brand, category (including its sub-categories), `min_price`, `max_price`.
- **Sorting:** price, name, created_at (asc/desc) via `OrderingFilter`.
- **Pagination:** `PageNumberPagination`, `page_size=12`, `page_size_query_param` allowed, max 100.
- **Validation + error handling:** price > 0 (Decimal, 2 dp), URL must be http/https, name/brand length limits, valid GTIN if given. One **consistent error format** via a custom DRF exception handler:
  ```json
  { "error": { "code": "validation_error", "message": "Invalid input.", "details": { "price": ["Must be greater than 0."] } } }
  ```
- **Permissions:** list/detail readable by anyone (`IsAuthenticatedOrReadOnly`). Create requires login. Update/delete only by the **owner (created_by) or staff**.
- **Swagger/OpenAPI** documented, with request/response examples on AI endpoints.
- **Logging:** structured logs (JSON or key=value), a request-id middleware, log every AI call (model, latency, tokens, success/failure). Never log API keys or full images.

### Frontend (React + JS)
- Login + Register screens. Protected routes for create/edit/delete.
- **Product list:** search bar (debounced), filters (brand, category, price range), sort dropdown, pagination. **All filters synced to the URL query string** (shareable, survives refresh).
- **Product details page.**
- **Add/Edit product form** with client-side validation that mirrors the backend.
- **Delete** with a confirmation modal.
- **Loading** (skeletons), **empty** ("No products match…" + clear-filters button), and **error** states (message + retry) on every data screen.
- Responsive (mobile-first), clean UI. Toasts for success/failure.

### GenAI feature (part of base): **Photo → autofilled product**
- `POST /api/ai/extract-product/` accepts **either** `image_url` **or** an uploaded image file (multipart, max 5 MB, jpeg/png/webp).
- Claude **vision** reads the pack shot and returns structured fields: `name`, `brand`, `category` (must be chosen from the existing category list, which is passed into the prompt), `variant` (e.g. flavour), `pack_size` (e.g. "250 g"), `description` (1–2 short sentences, max ~40 words: what the product is (type, brand, flavour/variant, pack size); never how the pack looks; no invented health claims), `tags` (3–6), plus a `confidence` per field and `notes` for anything unreadable.
- Use **JSON schema structured output** (`output_config.format`), then validate it with a DRF serializer. On invalid output, retry once, then return a clean error. (Forced tool use returns a 400 on Claude Sonnet 5.5, so structured output is the option used.)
- **Never auto-save.** The frontend prefills the Add Product form; the user reviews and edits, then saves. Show a small "AI-filled — please review" badge on each prefilled field.
- Also a text-only fallback `POST /api/ai/generate-description/` (name + brand + category → description + tags), matching the brief's own example.
- **Safety:** text printed on packaging is **untrusted input**. It must never change instructions or trigger actions. The output is data only, schema-validated. Throttle AI endpoints (DRF `ScopedRateThrottle`, e.g. 20/hour per user). Return a friendly error if the API key is missing or the quota is hit.
- **Image upload storage (decided in Block 7):** Cloudinary free **unsigned upload from the frontend**, so uploaded photos get a permanent `image_url`. If `VITE_CLOUDINARY_*` env vars are missing, uploads still work as a one-off read that is *not* stored. Pasting an image URL always works.

### GenAI feature #2 (part of base): **Natural-language search**
Why it's in the base: the assignment is titled "Product Management & **AI-Powered Search** Platform", so reviewers will expect AI search.
- `POST /api/ai/parse-search/` with `{ "query": "Britannia biscuits under ₹50, cheapest first" }`.
- Claude (fast model) turns the sentence into **structured filters only**, using JSON-schema structured output (brand / category / ordering lists passed as `enum`s):
  `{ "search": "biscuits", "brand": "Britannia", "category": "<existing category slug or null>", "min_price": null, "max_price": 50, "ordering": "price" }`
- Validate the output against a **whitelist**: allowed keys only. Brand and category must exist in the DB (pass the brand list + category list in the prompt; drop unknown values). Ordering must be one of the allowed orderings. Prices must be numbers ≥ 0. **The LLM never writes SQL** and never touches the DB directly.
- The frontend then calls the **normal** `GET /api/products/` with those filters. One search pipeline, no duplicate logic.
- UI: an "Ask AI" toggle (or ✨ button) on the search bar. The parsed filters appear as **removable chips** ("Brand: Britannia ✕", "Max ₹50 ✕", "Sort: price ↑ ✕"), so the user sees exactly how the query was understood and can correct it. The filters also sync to the URL like the manual filters.
- If AI is unavailable or the parse fails → fall back to plain keyword search with the raw text, plus a small notice.
- Same throttling and untrusted-input rules as the other AI endpoints. Cache identical queries briefly (e.g. 10 min, Django cache) to save tokens.

### Deployment (part of base)
- Deploy a **bare version early** (tonight) to surface deploy problems early.
- Render: `gunicorn`, `whitenoise` for admin static, build = install → collectstatic → migrate. `DEBUG=False`, `ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS` = Vercel domain, `CSRF_TRUSTED_ORIGINS`.
- Neon: enable `vector` and `pg_trgm` **via a Django migration** (`pgvector.django.VectorExtension`, `TrigramExtension`), not manually.
- Vercel: SPA rewrite (`vercel.json` → all routes to `index.html`). `VITE_API_BASE_URL` env var.
- Render free sleeps after inactivity (~50 s cold start). Add a keep-warm ping (GitHub Actions cron every ~10 min hitting `/api/health/`) and mention the cold start in the README.

---

## 4. Roadmap (strict order — stop wherever the deadline hits)

```
Auth + Product CRUD API
→ search, filter, sort, pagination + validation + Swagger
→ React screens (list, details, add/edit, delete, login/register)
→ Photo-to-form with Claude vision
→ Natural-language search (AI → whitelisted filters → chips)
→ Deploy (Render + Vercel + Neon)          ← base spec complete here
→ Look-alike SKU detector                   ← add-on #1 (headline feature)
→ (Add-ons #2–#4 in section 6 were dropped on 4 Nov 2026 for time: not building them)
→ README + ARCHITECTURE.md + CI polish
```

Seed data + tests are written **alongside** each step, not at the end. Redeploy after each add-on.

---

## 5. Data model (target shape — keep it simple)

```
User (Django default)

Category
  name, slug, parent (FK self, nullable)       # hierarchy: Food › Biscuits › Cream Biscuits
  full_path (property)                          # "Food › Biscuits › Cream Biscuits"

Product
  # brief-required
  name, brand, category (FK Category), description, price (Decimal 10,2), image_url
  # SKU-master extras (optional fields)
  gtin (CharField, blank, unique when non-empty → conditional UniqueConstraint)
  pack_size (e.g. "250 g"), variant (e.g. "Chocolate"), tags (ArrayField or JSON)
  created_by (FK User), created_at, updated_at
  # computed by services (not user-editable)
  image_phash (CharField, nullable), image_width, image_height, blur_score (float)
  name_embedding (VectorField(384), nullable)
  readiness_score (int 0–100), readiness_issues (JSON list), needs_review (bool)

LookalikePair
  product_a, product_b (ordered so a.id < b.id, unique together)
  image_distance (int, pHash Hamming), text_similarity (float)
  status: "unresolved" | "resolved_distinct" | "duplicate"
  resolved_by, resolved_at

ImportJob (add-on #3)
  file, status (pending/mapping/validating/importing/done/failed), column_mapping (JSON),
  total_rows, valid_rows, imported_rows, errors (JSON), created_by, timestamps

History (add-on #4): django-simple-history on Product
```

Put business logic in `services/` modules, one **service class** per file (e.g. `ReadinessService`, `LookalikeService`), not in views or model `save()`. Views stay thin. This is easy to explain in an interview. See section 15 for the coding rules.

---

## 6. Add-on specs

### Add-on #1 — Look-alike SKU detector (headline feature)
**Problem it solves:** same-brand variants with nearly identical packaging (sizes and flavours) are the hardest case in shelf recognition. The catalog must record the attribute that tells them apart.
- On image change: download the image (see safety in section 7), compute **pHash** (`imagehash`) plus width, height and blur. On name/brand/variant change: compute the **text embedding** (fastembed → pgvector).
- Candidates = same **brand** (+ same top-level category). Flag a pair if `pHash Hamming distance ≤ 10` (of 64 bits) **or** `cosine similarity ≥ 0.90`. Keep thresholds in settings so they're tunable.
- For each pair, **diff the distinguishing attributes** (`pack_size`, `variant`). If they're missing or identical → status `unresolved` (a "twin" the camera may confuse).
- UI: **Look-alikes page** with pairs side by side (images, key fields, differing attributes highlighted). Actions: "Mark as distinct" (after filling the missing attribute), "Mark as duplicate". The product detail page shows a "Possible look-alikes" box.
- Also warn on **create**: "This looks like an existing SKU: …" (non-blocking).
- Endpoint e.g. `GET /api/lookalikes/?status=unresolved`, `POST /api/lookalikes/{id}/resolve/`.

### Add-on #2 — Recognition-readiness score
Per-product checklist (each check = pass/fail + human message), score = % passed, stored on the product:
1. Has an image (`image_url` set and reachable)
2. Image is **sharp** (blur score = variance of Laplacian computed with **Pillow + numpy**, NOT OpenCV) and **big enough** (shortest side ≥ 300 px; threshold in settings)
3. **Valid GTIN** if present: GS1 mod-10 check digit, lengths 8/12/13/14. Plain code, no AI. Duplicate GTINs are blocked at the API level.
4. `pack_size` **and** `variant` filled
5. Category is a **leaf** (full path, not just "Food")
6. **Not a duplicate** (no other product with same normalized brand + name + pack_size)
7. **No unresolved look-alike twin**

- Catalog dashboard: "**X% of the catalog is recognition-ready**", count per failing check, and a "fix these first" list linking to the products.
- Product card: small score badge. Product detail: the full checklist.
- Endpoint e.g. `GET /api/readiness/summary/`. Recompute on product save (Celery task locally, inline in prod).

### Add-on #3 — Smart bulk import
**Problem:** brands send catalogs as messy spreadsheets with different column names.
1. Upload CSV or XLSX (`openpyxl`; max ~5 MB / 1,000 rows in prod).
2. Read headers + first ~5 rows → **Claude maps columns** to our fields (e.g. "Prod Desc" → description, "MRP" → price, "EAN code" → gtin). Strict JSON output, validated against the **allowed field list only**.
3. UI shows the mapping (user can change any dropdown) + **row-by-row validation preview** using the same serializer as the API (errors shown per row/cell).
4. Commit → **Celery task** imports valid rows in batches, updates `ImportJob` progress. The frontend polls `GET /api/imports/{id}/`. Afterwards it shows a summary (imported / skipped with reasons) and triggers readiness + look-alike recompute.
5. Provide a sample messy CSV in the repo (`samples/messy_brand_catalog.csv`) for the demo.

### Add-on #4 — Change history (optional)
- `django-simple-history` on Product. The detail page shows a timeline (who, when, what changed).
- If `image_url` changes → record "Packaging updated", set `needs_review=True`, and show a "New packaging — review" badge (the recognition team would need to re-learn this SKU).

---

## 7. Security & quality rules
- Secrets only in env vars. Commit `.env.example`, never `.env`.
- **Server-side image fetch safety (SSRF):** only http/https; resolve the host and block private/loopback/link-local IPs; 10 s timeout (`IMAGE_FETCH_TIMEOUT_SECONDS`; Open Food Facts often takes 5–6 s); max 5 MB; check content-type is an image; don't follow redirects to blocked hosts.
- Treat any text from images/spreadsheets as untrusted data, never as instructions.
- AI endpoints throttled. Graceful degradation if `ANTHROPIC_API_KEY` is missing: the app still works, AI buttons show "AI unavailable".
- Don't break the brief's required behaviour for an add-on.
- One clear commit per block with a meaningful message (Kaushal's GitHub: `eyekaushal`). One branch per block, merged into `main` via PR (see section 16).

---

## 8. Seed data
- ~100–150 **real Indian FMCG products** (biscuits, snacks, beverages, personal care; brands like Britannia, Parle, Nestlé, Amul, Haldiram's, Dabur, P&G) with real pack images from **Open Food Facts** (cite CC BY-SA licence + attribution in README).
- Fetch once with a script → save as `backend/seed/products.json` (committed) → management command `python manage.py seed_catalog` loads it (idempotent).
- **Deliberately include** for the demo: several same-brand size/flavour **twins** (e.g. Parle-G sizes, Good Day flavours), some products with missing pack_size/variant, an invalid GTIN, a small/blurry image. That way the look-alike and readiness features have something real to show.
- Create a **demo account** (credentials in README) with products owned by it.

---

## 9. Environment variables

**Backend (`backend/.env.example`)**
```
DJANGO_SECRET_KEY=
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,.onrender.com
DATABASE_URL=postgres://...            # Neon in prod
CORS_ALLOWED_ORIGINS=http://localhost:5173,https://<app>.vercel.app
CSRF_TRUSTED_ORIGINS=https://<app>.vercel.app
ANTHROPIC_API_KEY=
ANTHROPIC_MODEL_VISION=claude-sonnet-5-5   # verify current ID in Anthropic docs
ANTHROPIC_MODEL_FAST=claude-haiku-5-5      # column mapping / short text; verify ID
REDIS_URL=redis://redis:6379/0
CELERY_TASK_ALWAYS_EAGER=True              # True on Render (no worker), False in Docker
EMBEDDINGS_ENABLED=True                    # set False to use pg_trgm fallback
LOOKALIKE_PHASH_MAX_DISTANCE=10
LOOKALIKE_TEXT_MIN_SIMILARITY=0.90
LOOKALIKE_TRIGRAM_MIN_SIMILARITY=0.50     # used when EMBEDDINGS_ENABLED=False (Render)
```
**Frontend (`frontend/.env.example`)**
```
VITE_API_BASE_URL=http://localhost:8000/api
```

---

## 10. Repo layout (monorepo, repo name `shelfready`)
```
/backend      Django project (config/, apps: accounts, catalog, ai, imports), services/, tests/
/frontend     React + Vite + JS
/samples      messy_brand_catalog.csv
docker-compose.yml
.github/workflows/ci.yml, keep-warm.yml
README.md
ARCHITECTURE.md
CLAUDE.md
```

---

## 11. Tests (pytest + pytest-django) — the minimum
- GTIN validator (valid/invalid/lengths), price validation, error format.
- Permissions: anonymous can read, can't write; non-owner can't edit/delete.
- Filters/search/sort/pagination return the right products.
- Readiness checks (each rule), look-alike pairing on fixture data.
- AI endpoints with the **Claude client mocked** (no real API calls in CI). For natural-language search, test that unknown brands/categories, extra keys and bad orderings are dropped by the whitelist.
- Frontend: `npm run lint` + `npm run build` must pass in CI.

---

## 12. Docs to write

**README.md** (the brief requires all of these):
1. Project overview: open with the shelf-camera story (section 1) in 3–4 sentences
2. Live URLs: app, API, Swagger + demo credentials
3. Tech stack
4. Local setup (Docker Compose **and** manual)
5. Environment variables
6. Deployment details (Render/Vercel/Neon, cold start note, eager Celery in prod)
7. Key design decisions (why pHash + local embeddings instead of CLIP; why Celery only locally; why URL-first images; why JS not TS; services layer; permissions model)
8. GenAI features explained (photo-to-form, natural-language search, description generator, import column mapping), including the safety measures (whitelisted filters, no LLM-written SQL, schema-validated output)
9. Add-ons and **why each matters for shelf recognition**
10. Known limitations / what I'd do next

**ARCHITECTURE.md** is Kaushal's interview prep:
- A request's journey (React → axios → DRF view → serializer → service → DB → response).
- A "**Django for an Express developer**" mapping table (urls.py ≈ routes, views ≈ controllers, serializers ≈ validation + JSON shaping, models ≈ Mongoose schemas, middleware ≈ middleware, settings.py ≈ config/.env loading).
- How each add-on works, in plain words, plus likely interview questions with short answers.

---

## 13. Submission checklist (send to Indira by 4 Nov night)
- [ ] Live app URL (Vercel)
- [ ] GitHub repo URL (public)
- [ ] API docs URL (`<render-url>/api/docs/`)
- [ ] README with every section in section 12
- [ ] Short GenAI explanation (can be lifted from README section 8)
- [ ] Demo account works on the live URL; seed data loaded in prod
- [ ] Tested the full flow on the live URL in an incognito window (cold start included)

---

## 14. How to work with Kaushal
- Short, direct updates. Explain concepts before code when he asks.
- After each roadmap step: run the tests, give him a 3-line summary of what was built and how to try it.
- Ask before: adding a paid service, adding a dependency not listed here, changing a decision in section 2, or skipping a base-spec item.
- **Working files:** read `PRD.md`, `Design.md` and `plan.md` at the start of every stage. `plan.md` is split into blocks (Block 1, Block 2, …). When a block's tasks are done and tested, tick them (`- [x]`) in `plan.md`. Keep all three files up to date if a decision changes.

---

## 15. Coding rules

- **OOP, one class per file (backend):** every Python module holds one main class: models, serializers, views (class-based / ViewSets), and services (e.g. `services/readiness_service.py` → `class ReadinessService`). Small helpers such as a GTIN validator can be static methods on that class.
- **Frontend exception:** React uses normal **function components + hooks** (one component per file). Class components are the old style and don't work with hooks like TanStack Query. Non-UI frontend code (e.g. the API client) can be a class.
- **KISS (Keep It Simple, Stupid):** the simplest code that works. Short functions, clear names, no clever abstractions, no premature generalisation. If a pattern is hard to explain in an interview, don't use it.

---

## 16. Git rules (important)

- **Claude never runs `git commit` or `git push`** and never adds itself as a co-author. Kaushal does not want Claude listed as a contributor in the GitHub repo.
- No `Co-Authored-By` lines and no "Generated with Claude Code" lines in commit messages or PR descriptions.

### Branching strategy
- **`main`** = always working and deployable. Render and Vercel deploy from `main`. Never work on `main` directly.
- **One branch per block** in `plan.md`, cut from the latest `main`. Each block in `plan.md` lists its branch name.
- **Branch names:** `<type>/<short-name>`, with type = `feature/`, `fix/`, `docs/`, `chore/`. Examples: `feature/auth-api`, `fix/price-validation`, `docs/readme`.
- **Commit messages:** Conventional Commits, e.g. `feat(auth): add JWT login`, `fix(products): reject price 0`, `test(catalog): filter tests`.
- **Merge** through a GitHub Pull Request into `main` once tests and CI pass (a basic CI workflow is added in Block 1 so every PR is checked). Use "Create a merge commit" so each block's commit stays visible in the history. **Keep every branch after merging (never delete them)**, so each block stays visible on GitHub.
- A bug found later gets its own `fix/...` branch. Don't reopen an old block branch.

### Commands Claude gives at each stage
**Starting a block:**
```bash
git checkout main
git pull origin main
git checkout -b feature/auth-api
```
**End of a block (one add, one commit):**
```bash
git add -A
git commit -m "feat(auth): JWT register, login, refresh, logout"
git push -u origin feature/auth-api
```
**Merging:** open a PR `feature/auth-api → main` on GitHub (or `gh pr create --base main --fill`), merge it, then:
```bash
git checkout main
git pull origin main
```

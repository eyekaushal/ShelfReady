# Plan — ShelfReady

> Build in block order. Tick `- [x]` when a task is done **and tested**.
> Deadline: submit by **4 Nov 2026 night** (hard deadline 5 Nov 2026, 9:00 AM IST). Stop wherever the deadline hits.
> **Per block:** create the block's branch from `main` → build → run tests → 3-line summary → one `git add -A` + one commit → push branch → PR into `main` → merge → tick here.
> Claude only gives the git commands; Kaushal runs them (see CLAUDE.md §16). `main` is always deployable.

**Progress:** 10 of 11 blocks done (Blocks 11–13 dropped on 4 Nov 2026 for time)

---

## Block 1 — Project setup ✅
**Branch:** `chore/project-setup`
- [x] Monorepo folders: `backend/`, `samples/` (`frontend/` is created by Vite in Block 6)
- [x] Django 5.2 LTS project (`config/`) + apps: `accounts`, `catalog`, `ai`, `imports`, `common`
- [x] Settings from env vars (django-environ), `.env.example`, `.gitignore`
- [x] `docker-compose.yml`: db (pgvector), redis, backend, worker (frontend service added in Block 6)
- [x] Migration enabling `vector` + `pg_trgm`
- [x] `/api/health/` endpoint (no DB hit, so keep-warm pings don't use up Neon's compute hours)
- [x] Custom exception handler (consistent error format, JSON 404/500) + request-id middleware + JSON logging
- [x] pytest + pytest-django + ruff configured (11 tests passing)
- [x] Basic GitHub Actions CI (ruff + check + migrations check + pytest) on push and on PRs into `main`

## Block 2 — Auth API ✅
**Branch:** `feature/auth-api`
- [x] simplejwt with refresh rotation + blacklist (access 30 min, refresh 7 days)
- [x] Register (returns tokens, unique email, Django password rules), login, refresh, logout, `me` endpoints
- [x] Rate limit on auth endpoints (`auth` scope, 20/min) against password guessing
- [x] Tests: register/login/refresh/logout/me flow, error format, throttling (28 tests passing)

## Block 3 — Product CRUD API ✅
**Branch:** `feature/product-crud`
- [x] `Category` model (parent hierarchy, `full_path`, unique name per parent)
- [x] `Product` model (brief fields + SKU extras + computed fields, DB constraints: unique GTIN when set, price > 0)
- [x] `GtinValidator` class (GS1 mod-10, lengths 8/12/13/14)
- [x] Product serializer with validation (price, http/https URL, lengths, GTIN, unique GTIN, tag + whitespace cleanup)
- [x] ProductViewSet + `IsOwnerOrStaff` permission
- [x] Categories (read-only, with `full_path` + `is_leaf`) + brands endpoints
- [x] Django admin for Category and Product
- [x] Tests: validation, error format (incl. Django 404/403 → standard codes), permissions (76 tests passing)

## Block 4 — Search, filter, sort, pagination + Swagger ✅
**Branch:** `feature/search-filter-sort`
- [x] `SearchFilter` (name, brand, description, case-insensitive)
- [x] `django-filter` `ProductFilter`: brand (exact, ignores case), category slug (with sub-categories), min/max price (+ min ≤ max check)
- [x] `StableOrderingFilter`: price, name, created_at, with an `id` tie-breaker so pages never repeat/skip
- [x] `StandardPagination` (12, `page_size`, max 100)
- [x] drf-spectacular: `/api/docs/`, `/api/redoc/`, `/api/schema/` (schema validated in CI with `--fail-on-warn`)
- [x] Tests: filters/search/sort/pagination/docs (106 tests passing)

## Block 5 — Seed data ✅
**Branch:** `feature/seed-data`
- [x] `OpenFoodFactsFetcher` script → `backend/seed/products.json` (141 products, 20 Indian brands, 24 categories)
- [x] Cleans names / pack sizes, maps categories by name + brand default, picks flavour variants, illustrative prices
- [x] Demo problems: twins (Parle-G sizes, Lay's sizes…), missing pack size, invalid GTIN, 200 px image, non-leaf category, one duplicate
- [x] `seed_catalog` command + `CatalogSeeder` service (idempotent) + demo account `demo` / `SEED_DEMO_PASSWORD`
- [x] Tests: seeder + guards on the committed JSON (118 tests passing)

## Block 6 — React frontend (base screens) ✅
**Branch:** `feature/frontend-base`
- [x] Vite + React 19 (JS) + Tailwind v4 + React Router + TanStack Query + lucide-react icons (Node 22, `.nvmrc`)
- [x] Add `frontend` service to `docker-compose.yml`
- [x] `ApiClient` class: axios + JWT refresh interceptor
- [x] AuthContext, Login, Register, ProtectedRoute
- [x] Product list: debounced search, filters, sort, pagination, URL-synced
- [x] Product details page
- [x] Add/Edit form with client-side validation
- [x] Delete confirmation modal
- [x] Loading skeletons, empty state, error + retry, toasts, responsive
- [x] `npm run lint` (oxlint, 0 warnings) + `npm run build` pass; full create → edit → delete flow checked in a real browser

## Block 7 — AI: Photo → product form ✅
**Branch:** `feature/ai-photo-to-form`
- [x] `ClaudeClient` class: env models, JSON-schema structured output, DRF validation + one retry, refusal fallback (Sonnet), log line per call, SDK errors → `ai_*` codes
- [x] `ImageService`: SSRF-safe fetch (http/https, public IPs only, every redirect re-checked, 10 s, 5 MB, image content-type), Pillow-verified JPEG/PNG/WebP, shrink to 1568 px for Claude
- [x] `POST /api/ai/extract-product/` (URL or upload; category whitelist; never saves) + `GET /api/ai/status/`
- [x] `POST /api/ai/generate-description/` (fast model)
- [x] Throttling (`ai` scope, 20/hour per user) + "AI unavailable" when there's no key (checked before any image fetch)
- [x] Frontend: "Fill from photo" panel (upload / URL), Cloudinary unsigned upload when configured, "AI-filled · review" badges (amber when unsure), "Write with AI" for description + tags
- [x] Tests with Claude mocked (177 backend tests passing); UI checked in the browser with a mocked AI answer

## Block 8 — AI: Natural-language search ✅
**Branch:** `feature/ai-nl-search`
- [x] `NLSearchService` + `POST /api/ai/parse-search/` (JSON-schema structured output, Haiku, brand/category/ordering as enums)
- [x] Whitelist (`ParsedSearchSerializer`): allowed keys only, brand + category must exist (unknown → dropped), allowed orderings, prices numbers ≥ 0, reversed range swapped
- [x] 10-minute cache for identical queries (case/space-insensitive)
- [x] Open to anonymous visitors, own rate limit (`ai_search`, 30/hour per user or IP)
- [x] Frontend: "Ask AI" toggle on the search bar, "AI understood …" notice + removable chips, filters synced to the URL
- [x] Fallback to keyword search with the raw text + a notice when AI fails
- [x] Tests: unknown brand/category, extra keys, bad orderings/prices dropped; cache; throttle; fallback 503 (202 tests passing); checked live with a real Haiku call

## Block 9 — Deploy (base spec complete here ✅)
**Branch:** `chore/deploy`
- [x] Deploy files: `render.yaml`, `backend/build.sh` (install, collectstatic, migrate, seed: free plan has no shell), `frontend/vercel.json`, Node 22 + Python 3.12 pinned
- [x] Gunicorn: 1 worker + 4 threads, `--timeout 90` (rehearsed in production mode on an empty DB)
- [x] Fix: page load only clears the saved login on a 401; API timeout 70 s for Render cold starts
- [x] `GlobalAiThrottle`: shared daily cap on AI calls (`ai_global`, 300/day), since `X-Forwarded-For` can be forged
- [x] Keep-warm GitHub Actions cron (needs the `RENDER_URL` repo variable)
- [x] Neon project created (Singapore); extensions enabled by the migration
- [x] Render live at https://shelfready-api.onrender.com, env vars + CORS set, seed + demo account in prod
- [x] Vercel live at https://shelf-ready.vercel.app with the API + Cloudinary env vars
- [x] `RENDER_URL` variable set and keep-warm run succeeded
- [x] Seed images copied to Cloudinary (first load was 4–25 s per image from Open Food Facts)
- [x] Full flow tested in an incognito window

## Block 10 — Add-on #1: Look-alike SKU detector
**Branch:** `feature/lookalike-detector`
- [x] `ImageService.measure`: pHash, width, height, blur (Pillow + numpy)
- [x] `EmbeddingService`: fastembed bge-small → pgvector locally; pg_trgm on Render (`EMBEDDINGS_ENABLED=False`: the model peaks at ~320 MB, the plan has 512 MB)
- [x] `LookalikePair` model + `LookalikeService` (same brand + top category, thresholds from settings; trigram 0.50 tuned on seed data); people's decisions survive rechecks
- [x] `analyze_product` Celery task on save (never fails the save) + `analyze_catalog` command in `build.sh`
- [x] Endpoints: list (`status`, `product`), resolve (distinct needs a differing attribute), check
- [x] Look-alikes page + "Possible look-alikes" box + warning on the form
- [x] Tests on fixture data (248 passing); real data checked in both modes; UI checked in the browser
- [x] Redeployed; live check: 37 unresolved + 21 distinct pairs, pg_trgm mode, page and API working

## Block 11 — Add-on #2: Recognition-readiness score: NOT BUILDING
Dropped for time, so the remaining effort goes to a solid base spec and docs.

## Block 12 — Add-on #3: Smart bulk import: NOT BUILDING
Dropped for time, so the remaining effort goes to a solid base spec and docs.

## Block 13 — Add-on #4: Change history (optional): NOT BUILDING
Dropped for time, so the remaining effort goes to a solid base spec and docs.

## Fixes from live testing ✅
**Branch:** `fix/live-test-bugs`
- [x] AI search: words that match nothing are dropped when other filters were understood; prompt ignores question and stock words
- [x] Any logged-in user can resolve look-alikes; visitors get a sign-in prompt
- [x] Readiness removed from the UI and the API

## Block 14 — Docs, CI and submission
**Branch:** `docs/readme-architecture-ci`
- [ ] CI polish: add frontend lint + build, pgvector Postgres service
- [ ] README.md (all sections in CLAUDE.md §12), incl. Open Food Facts attribution (ODbL data, CC BY-SA images) and "prices are illustrative"
- [ ] ARCHITECTURE.md (request journey, Django-for-Express table, interview Q&A)
- [ ] Submission checklist (CLAUDE.md §13) sent to Indira

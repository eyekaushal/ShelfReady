# Plan — ShelfReady

> Build in block order. Tick `- [x]` when a task is done **and tested**.
> Deadline: submit by **4 Nov 2026 night** (hard deadline 5 Nov 2026, 9:00 AM IST). Stop wherever the deadline hits.
> **Per block:** create the block's branch from `main` → build + small commits → run tests → 3-line summary → push branch → PR into `main` → merge → tick here.
> Claude only gives the git commands; Kaushal runs them (see CLAUDE.md §16). `main` is always deployable.

**Progress:** 1 of 14 blocks done

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

## Block 2 — Auth API
**Branch:** `feature/auth-api`
- [ ] simplejwt with refresh blacklist
- [ ] Register, login, refresh, logout, `me` endpoints
- [ ] Tests: register/login/logout flow

## Block 3 — Product CRUD API
**Branch:** `feature/product-crud`
- [ ] `Category` model (parent hierarchy, `full_path`)
- [ ] `Product` model (brief fields + SKU extras + computed fields)
- [ ] `GtinValidator` class (GS1 mod-10, lengths 8/12/13/14)
- [ ] Product serializer with validation (price, URL, lengths, GTIN, unique GTIN)
- [ ] ProductViewSet + owner-or-staff permission
- [ ] Categories + brands endpoints
- [ ] Tests: validation, error format, permissions

## Block 4 — Search, filter, sort, pagination + Swagger
**Branch:** `feature/search-filter-sort`
- [ ] `SearchFilter` (name, brand, description)
- [ ] `django-filter`: brand, category (with sub-categories), min/max price
- [ ] `OrderingFilter`: price, name, created_at
- [ ] Pagination (12, `page_size`, max 100)
- [ ] drf-spectacular: `/api/docs/`, `/api/redoc/`, `/api/schema/`
- [ ] Tests: filters/search/sort/pagination

## Block 5 — Seed data
**Branch:** `feature/seed-data`
- [ ] Script to fetch ~100–150 Indian FMCG products from Open Food Facts → `backend/seed/products.json`
- [ ] Include twins, missing pack_size/variant, invalid GTIN, blurry/small image
- [ ] `seed_catalog` management command (idempotent) + demo account

## Block 6 — React frontend (base screens)
**Branch:** `feature/frontend-base`
- [ ] Vite + React (JS) + Tailwind + React Router + TanStack Query
- [ ] Add `frontend` service to `docker-compose.yml`
- [ ] `ApiClient` class: axios + JWT refresh interceptor
- [ ] AuthContext, Login, Register, ProtectedRoute
- [ ] Product list: debounced search, filters, sort, pagination, URL-synced
- [ ] Product details page
- [ ] Add/Edit form with client-side validation
- [ ] Delete confirmation modal
- [ ] Loading skeletons, empty state, error + retry, toasts, responsive
- [ ] `npm run lint` + `npm run build` pass

## Block 7 — AI: Photo → product form
**Branch:** `feature/ai-photo-to-form`
- [ ] `ClaudeClient` class (env models, logging, friendly errors)
- [ ] `ImageService.safe_fetch` (SSRF-safe, 5 s, 5 MB, image content-type)
- [ ] `POST /api/ai/extract-product/` (URL or upload, forced tool use, serializer validation, retry once)
- [ ] `POST /api/ai/generate-description/`
- [ ] Throttling (20/hour) + "AI unavailable" when there's no key
- [ ] Frontend: "Fill from photo" panel + "AI-filled — please review" badges
- [ ] Tests with Claude mocked

## Block 8 — AI: Natural-language search
**Branch:** `feature/ai-nl-search`
- [ ] `NLSearchService` + `POST /api/ai/parse-search/` (forced tool use)
- [ ] Whitelist validation (keys, brand/category exist, ordering, prices ≥ 0)
- [ ] 10-minute cache for identical queries
- [ ] Frontend: ✨ Ask AI toggle + removable filter chips, synced to the URL
- [ ] Fallback to keyword search + notice
- [ ] Tests: unknown brand/category, extra keys, bad ordering are dropped

## Block 9 — Deploy (base spec complete here ✅)
**Branch:** `chore/deploy`
- [ ] Neon DB + extensions migration
- [ ] Render: gunicorn, whitenoise, build command, env vars, eager Celery
- [ ] Vercel: `vercel.json` SPA rewrite, `VITE_API_BASE_URL`
- [ ] Seed data + demo account in prod
- [ ] Keep-warm GitHub Actions cron
- [ ] Render + Vercel set to auto-deploy from `main` only
- [ ] Full flow tested in an incognito window

## Block 10 — Add-on #1: Look-alike SKU detector
**Branch:** `feature/lookalike-detector`
- [ ] `ImageService`: pHash, width, height, blur (Pillow + numpy)
- [ ] `EmbeddingService`: fastembed bge-small → pgvector (pg_trgm fallback)
- [ ] `LookalikePair` model + `LookalikeService` (same brand + top category, thresholds from settings)
- [ ] Endpoints: list + resolve
- [ ] Look-alikes page + "Possible look-alikes" box + warning on create
- [ ] Tests on fixture data · redeploy

## Block 11 — Add-on #2: Recognition-readiness score
**Branch:** `feature/readiness-score`
- [ ] `ReadinessService` with the 7 checks
- [ ] Recompute on save (Celery task, eager in prod)
- [ ] `GET /api/readiness/summary/`
- [ ] Dashboard page + score badge on cards + checklist on details
- [ ] Tests for each rule · redeploy

## Block 12 — Add-on #3: Smart bulk import
**Branch:** `feature/bulk-import`
- [ ] `ImportJob` model + CSV/XLSX upload
- [ ] Claude column mapping (allowed fields only)
- [ ] Mapping UI + row-by-row validation preview
- [ ] Celery import in batches + progress polling + summary
- [ ] `samples/messy_brand_catalog.csv` · redeploy

## Block 13 — Add-on #4: Change history (optional)
**Branch:** `feature/change-history`
- [ ] django-simple-history on Product
- [ ] Timeline on the details page
- [ ] "New packaging — review" badge when `image_url` changes

## Block 14 — Docs, CI and submission
**Branch:** `docs/readme-architecture-ci`
- [ ] CI polish: add frontend lint + build, pgvector Postgres service
- [ ] README.md (all sections in CLAUDE.md §12)
- [ ] ARCHITECTURE.md (request journey, Django-for-Express table, interview Q&A)
- [ ] Submission checklist (CLAUDE.md §13) sent to Indira

# Design — ShelfReady

> *How* we build it: architecture, code structure, data model, API and UI.
> Requirements are in `PRD.md`; the build order is in `plan.md`.

---

## 1. Architecture

```
React (Vercel) ──axios + JWT──▶ Django REST API (Render) ──▶ PostgreSQL + pgvector (Neon)
                                       │
                                       ├──▶ Anthropic Claude API (vision + fast model)
                                       └──▶ Celery task (eager in prod, Redis worker in local Docker)
```

**Request journey:** React page → axios client → DRF view → serializer (validation) → service class (business logic) → model / DB → serializer → JSON response.

## 2. Code structure rules

- **Backend: one class per file.** Views and ViewSets, serializers, models and services are all classes.
- **Thin views.** Views only parse the request, call a service and return a response.
- **Services hold business logic.** For example `ReadinessService.compute(product)`, never inside `Model.save()`.
- **Frontend: function components + hooks**, one component per file. Non-UI helpers (the API client) can be a class.
- **KISS:** no extra layers, no generic base classes unless they're used 3 or more times.

## 3. Backend layout

```
backend/
  config/                 settings.py, urls.py, wsgi.py, celery.py
  accounts/               serializers/ (RegisterSerializer, UserSerializer), views/ (RegisterView, LoginView,
                          LogoutView, MeView), urls.py
  catalog/                models/ (category.py, product.py, lookalike_pair.py), serializers/ (ProductSerializer,
                          CategorySerializer), views/ (ProductViewSet, CategoryViewSet, BrandListView),
                          permissions/ (IsOwnerOrStaff), admin/, filters/ (ProductFilter)
  ai/                     views/ (AIStatusView, ExtractProductView, GenerateDescriptionView),
                          serializers/ (request + AI-output validation serializers)
  imports/                models/import_job.py, views/, tasks.py
  services/
    claude_client.py          class ClaudeClient            (one wrapper for all Claude calls + logging)
    ai_service_error.py       class AIServiceError          (DRF exception with ai_* codes)
    product_extract_service.py class ProductExtractService  (photo → fields)
    nl_search_service.py      class NLSearchService         (sentence → whitelisted filters)
    description_service.py    class DescriptionService
    image_service.py          class ImageService            (safe fetch, pHash, size, blur)
    embedding_service.py      class EmbeddingService        (fastembed or pg_trgm fallback)
    lookalike_service.py      class LookalikeService
    readiness_service.py      class ReadinessService
    gtin_validator.py         class GtinValidator
    import_service.py         class ImportService
    catalog_seeder.py         class CatalogSeeder           (loads seed JSON, idempotent)
  common/                 exception_handler.py (ApiExceptionHandler), request_id_middleware.py,
                          log/ (RequestContext, RequestIdFilter, JsonFormatter), views/ (HealthView, ErrorViews),
                          pagination/ (StandardPagination), filters/ (StableOrderingFilter)
  seed/                   fetch_open_food_facts.py (OpenFoodFactsFetcher, run once) → products.json (committed)
  catalog/management/     commands/seed_catalog.py → services/catalog_seeder.py (CatalogSeeder)
  tests/
```

## 4. Data model

| Model | Key fields |
|---|---|
| **Category** | `name`, `slug`, `parent` (self FK, nullable), `full_path` property |
| **Product** | brief: `name, brand, category, description, price (Decimal 10,2), image_url` · extras: `gtin` (unique when non-empty), `pack_size`, `variant`, `tags` · meta: `created_by, created_at, updated_at` · computed: `image_phash, image_width, image_height, blur_score, name_embedding (Vector 384), readiness_score, readiness_issues, needs_review` |
| **LookalikePair** | `product_a, product_b` (a.id < b.id, unique together), `image_distance`, `text_similarity`, `status` (unresolved / resolved_distinct / duplicate), `resolved_by, resolved_at` |
| **ImportJob** | `file, status, column_mapping, total_rows, valid_rows, imported_rows, errors, created_by`, timestamps |
| **History** | `django-simple-history` on Product |

## 5. API endpoints

| Method | Path | Auth | Purpose |
|---|---|---|---|
| POST | `/api/auth/register/` | – | Create account → `{user, access, refresh}` |
| POST | `/api/auth/login/` | – | JWT pair |
| POST | `/api/auth/refresh/` | – | New access + refresh (rotation) |
| POST | `/api/auth/logout/` | – (refresh token is the proof) | Blacklist refresh → 205 |
| GET | `/api/auth/me/` | user | Current user |
| GET | `/api/products/` | – | List + `search`, `brand`, `category` (slug, incl. sub-categories), `min_price`, `max_price`, `ordering`, `page`, `page_size` → `{count, next, previous, results}` |
| POST | `/api/products/` | user | Create (`category` = id; response adds `category_detail`) |
| GET / PUT / PATCH / DELETE | `/api/products/{id}/` | owner / staff for writes | Detail / update / delete |
| GET | `/api/categories/` · `/api/brands/` | – | Dropdown data (not paginated). Categories are managed in admin |
| GET | `/api/ai/status/` | – | `{enabled}`: AI buttons show "AI unavailable" when false |
| POST | `/api/ai/extract-product/` | user, throttled | Photo (URL or multipart `image`) → `{fields, confidence, notes}` |
| POST | `/api/ai/generate-description/` | user, throttled | Text → description + tags |
| POST | `/api/ai/parse-search/` | throttled, cached 10 min | Sentence → filters |
| GET | `/api/lookalikes/?status=` · POST `/api/lookalikes/{id}/resolve/` | user | Add-on #1 |
| GET | `/api/readiness/summary/` | – | Add-on #2 |
| POST / GET | `/api/imports/` · `/api/imports/{id}/` | user | Add-on #3 |
| GET | `/api/health/` | – | Keep-warm ping |
| GET | `/api/docs/` · `/api/redoc/` · `/api/schema/` | – | API docs |

**Error format (every error):**
```json
{ "error": { "code": "validation_error", "message": "Invalid input.", "details": { "price": ["Must be greater than 0."] } } }
```

## 6. AI design

- **One `ClaudeClient` class** handles every call: model from env, structured JSON output, DRF validation with
  one retry, refusal fallback on models that support it, one `ai call` log line (task, model, latency, tokens,
  outcome; never the key or the image), and SDK errors → clean `AIServiceError` codes:
  `ai_not_configured` (503), `ai_busy` (503), `ai_refused` (422), `ai_invalid_output` (502), `ai_error` (502).
- **Structured outputs** (`output_config.format` with a JSON schema). Forced tool use is not used: it returns a
  400 on Claude Sonnet 5.5.
- **Untrusted input:** text on packaging or in spreadsheets is data, never instructions (said in the system
  prompt; output is only data, validated, unknown keys dropped, never auto-saved).
- **Photo → form:** `ImageService` fetches URLs safely (SSRF: http/https only, public IPs only, each redirect
  re-checked, 10 s, 5 MB, image content-type) or reads the upload, verifies JPEG/PNG/WebP with Pillow and shrinks
  to ≤1568 px. Categories are a whitelist (`enum` of slugs) and come back as an id for the form.
  Price and GTIN are never filled by AI. Descriptions are 1–2 short sentences (≤300 chars, enforced by the
  serializer): what the product is, never how the pack looks.
- **Uploads:** browser → Cloudinary (unsigned preset) → permanent URL → extract by URL. Without Cloudinary env
  vars: one-off multipart upload, not stored.
- **NL search whitelist (Block 8):** allowed keys only; brand and category must exist in the DB; ordering from the
  allowed list; prices ≥ 0. The LLM never writes SQL.
- **Models:** `ANTHROPIC_MODEL_VISION` = `claude-sonnet-5-5` (photo extraction, effort `medium`),
  `ANTHROPIC_MODEL_FAST` = `claude-haiku-5-5` (description, search parsing, column mapping, effort `low`).

## 7. Frontend layout

Stack: React 19 + Vite + plain JS, Tailwind v4, React Router 7, TanStack Query 5, axios, lucide-react icons,
oxlint for linting. Node 22 (`frontend/.nvmrc`).

```
frontend/src/
  api/          apiClient.js (class ApiClient: axios, Bearer token, silent JWT refresh shared by
                parallel requests, every error → ApiError), authApi.js, productsApi.js, catalogApi.js
                aiApi.js (60 s timeout for AI calls)
  auth/         AuthContext.jsx (AuthProvider), authContext.js, useAuth.js (+ canEditProduct), ProtectedRoute.jsx
  pages/        ProductListPage, ProductDetailPage, ProductFormPage (new + edit), LoginPage, RegisterPage,
                NotFoundPage  (+ LookalikesPage, ReadinessDashboardPage, ImportPage in add-ons)
  components/
    layout/     AppShell (sidebar on desktop, drawer on mobile), Sidebar, AuthLayout, Wordmark
    catalog/    SearchBar, FilterPanel, FilterChips, SortMenu, ViewToggle, Pagination, ProductTable,
                ProductGrid, ProductImage, ProductListSkeleton, ReadinessRing
    ui/         Button, Input, Select, Textarea, PasswordInput, FormField, FormSection, Modal, ConfirmModal,
                Menu, Toast, Badge, Chip, Avatar, Skeleton, Spinner, EmptyState, ErrorState, PageHeader,
                DescriptionList
  components/ai/ PhotoFillPanel (upload / URL → Claude → prefill), AiBadge ("AI-filled · review", amber if unsure)
  hooks/        useUrlFilters, useProducts / useProduct, useProductMutations, useCatalogOptions, useDebounce,
                useAiStatus
  lib/          cloudinary.js (optional unsigned upload), apiError.js (class ApiError), validation.js (mirrors the backend serializer, incl. GTIN
                mod-10), format.js (₹ en-IN, dates), readiness.js, cn.js
```

- **Server state:** TanStack Query (30 s stale time; retries once, only on network / 5xx errors).
- **URL state:** search, brand, category, price range, ordering, page, page size and view (table / grid)
  live in the query string (`useUrlFilters`); defaults are left out; any change except paging resets to page 1.
- **Tokens:** access + refresh in localStorage; on 401 `token_not_valid` the client refreshes once and retries.
- **Permissions in the UI:** Edit / Delete only shown when `canEditProduct` (owner or staff), same rule as
  `IsOwnerOrStaff`; the backend still enforces it.
- **Every data screen** has loading (skeleton), empty (message + clear filters) and error (message + retry) states.

## 8. UI design

- **Style:** Linear / Attio-like: white canvas, hairline borders, Inter, one blue accent, status colour only as
  rings, dots and chips. Mobile-first.
- **Shell:** left sidebar (Catalog, Add product, API docs, user + logout); top bar with a drawer on mobile.
  Look-alikes, Readiness and Import links get added with the add-ons.
- **List page:** search bar (debounced, "/" to focus) → Filter popover (brand, category, price) + sort menu +
  table/grid toggle → removable filter chips (reused by AI search in Block 8) → table or grid → pagination.
- **Product form:** "Fill from photo" panel on top (new products), then sections Basics, Description, Pack shot
  (live image preview), Identifiers; client-side validation, backend field errors mapped onto the same fields.
  AI-filled fields get a blue "AI-filled · review" badge (amber "AI · check this" when confidence is low) that
  disappears once the user edits the field. "Write with AI" under the description fills description + tags.
- **AI look:** no new colours: the same blue accent with a Sparkles icon; "AI unavailable" grey tag when off.
- **Details page:** image, highlight tiles (price, pack size, variant, GTIN, category, readiness ring), description,
  tags, full field list. Add-ons add the readiness checklist, "Possible look-alikes" box and history timeline.
- **Readiness ring:** dashed "Not scored yet" until Block 11 computes scores (avoids a misleading 0%).
- **Feedback:** toasts (bottom centre, 4 s), confirm modal for delete.

## 9. Seed data

- **Source:** Open Food Facts (ODbL data, CC BY-SA images), India, 20 brands × up to 7 products.
- **Prices are illustrative** (OFF has no prices): leaf-category ₹/g or ₹/ml × pack size, rounded to ₹5.
- **Deliberate problems** (marked `demo_note` in the JSON) so readiness + look-alike features have real cases.
- **Loader writes via the ORM, not the API**, so the deliberately bad rows (e.g. invalid GTIN) can exist.
- **Idempotent:** matched on category slug / username / GTIN, so re-running updates instead of duplicating.

## 10. Infrastructure

- **Local:** `docker-compose.yml` → `db` (pgvector/pgvector:pg16), `redis`, `backend`, `worker`, `frontend`.
- **Prod:** Render (gunicorn + whitenoise, eager Celery), Vercel (SPA rewrite), Neon (extensions enabled via migration).
- **CI:** GitHub Actions → ruff + pytest (pgvector Postgres service) + frontend lint + build. Runs on every push and on every PR into `main`. Keep-warm cron every ~10 min.

## 11. Git workflow

```
main ──●────────●────────●──────▶   (always deployable → Render + Vercel auto-deploy)
        \      / \      /
         ●──●─●   ●──●─●
   feature/auth-api  feature/product-crud
```

- One branch per `plan.md` block, cut from the latest `main`. Branch names are listed in `plan.md`.
- Names are `feature/…`, `fix/…`, `docs/…` or `chore/…`. Commits follow Conventional Commits (`feat(auth): …`).
- Merge via a GitHub PR after CI passes, using a merge commit. Branches are kept after merging, never deleted.
- Kaushal runs all git commands; Claude only provides them (CLAUDE.md §16).

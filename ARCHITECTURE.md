# ShelfReady architecture

How the code fits together, in plain words, for a code walkthrough.

## The big picture

```
React (Vercel) ──axios + JWT──▶ Django REST API (Render) ──▶ PostgreSQL + pgvector (Neon)
                                       │
                                       ├──▶ Claude API (reads photos, parses search)
                                       └──▶ Image hosts (pack photos, fetched safely)
```

```
backend/
  config/      settings, main URLs, Celery app
  accounts/    register, login, logout, me
  catalog/     Product, Category, LookalikePair: models, serializers, views, filters, tasks
  ai/          AI endpoints and the serializers that validate AI answers
  services/    business logic, one class per file
  common/      error format, request id, JSON logs, pagination, throttling
  seed/        demo data and the scripts that built it
  tests/
frontend/src/
  api/         the only code that calls the backend
  auth/        who is logged in
  pages/       one component per route
  components/  ui/ (generic), layout/, catalog/, ai/, lookalikes/
  hooks/       server data and URL state
  lib/         validation, formatting, errors
```

## A request's journey

**Example: saving a new product.**

| Step | Where | What happens |
|---|---|---|
| 1 | `pages/ProductFormPage.jsx` | `validateProduct` checks the form first, so mistakes show instantly |
| 2 | `hooks/useProductMutations.js` | TanStack Query runs the save and refreshes cached lists afterwards |
| 3 | `api/apiClient.js` | axios adds `Authorization: Bearer <token>`. If the token has expired, it refreshes and retries once |
| 4 | `common/request_id_middleware.py` | Gives the request an id and logs it when finished |
| 5 | `config/urls.py` → `catalog/urls.py` | Routes the URL to `ProductViewSet` |
| 6 | `simplejwt` + `IsAuthenticatedOrReadOnly` | Checks who you are and that you may write |
| 7 | `catalog/serializers/product_serializer.py` | Validates again. The browser can't be trusted, so this check is the real one |
| 8 | `ProductViewSet.perform_create` | Saves with `created_by=request.user`, never a value from the request body |
| 9 | `catalog/tasks.py` | `analyze_product.delay(...)` queues the look-alike work |
| 10 | Serializer again | Turns the product into JSON for the 201 response |

If anything fails, `common/exception_handler.py` turns it into the one standard error shape, and `lib/apiError.js` maps field errors back onto the form.

**Reads are similar:** `GET /api/products/?brand=Parle&ordering=price` goes through `ProductFilter`, `SearchFilter`, `StableOrderingFilter` and `StandardPagination`. On the frontend, `useUrlFilters` keeps the filters in the URL, and `useProducts` fetches with them.

## Django for an Express developer

| Django / DRF | Express / MERN | Note |
|---|---|---|
| `urls.py` | `app.get('/path')`, routers | Maps URLs to handlers |
| Views, ViewSets | Controllers | A `ModelViewSet` gives you all five CRUD routes |
| Serializers | Joi/Zod + manual JSON shaping | Validates input *and* shapes output |
| Models | Mongoose schemas | Tables instead of collections |
| Migrations | (none in Mongoose) | Versioned, repeatable database changes |
| Middleware | Middleware | Same idea, runs around every request |
| `settings.py` | config + `dotenv` | One place for configuration |
| Permissions | Auth middleware | Declared on the view |
| `select_related` | `.populate()` | Loads related rows in one SQL query |
| Management commands | npm scripts | `python manage.py seed_catalog` |
| Celery + Redis | BullMQ + Redis | Background jobs |
| `pytest` | Jest | Tests |
| `requirements.txt` | `package.json` | Dependencies |

## How the main features work

### Login (JWT)
- **Login** returns a short-lived access token (30 minutes) and a refresh token (7 days).
- **Every request** sends the access token. On a 401 `token_not_valid`, `ApiClient` gets a new one and retries. Several failing requests share one refresh call.
- **Rotation:** each refresh returns a new refresh token and blacklists the old one, so a stolen one stops working once used.
- **Logout** blacklists the refresh token. JWTs can't be deleted, so a blacklist is how you revoke them.

### Search, filters, sorting
- **Search** looks in name, brand and description. Every word must match, in any of those fields.
- **Category** takes a slug and includes all sub-categories, using `Category.descendant_ids()`.
- **`StableOrderingFilter`** adds `id` as a tie-breaker. Without it, Postgres can order equal prices differently on each query, so a product could appear on two pages.

### Photo → product form
1. `PhotoFillPanel` uploads to Cloudinary if configured, then sends the URL. Otherwise it sends the file itself.
2. `ImageService` fetches the image safely, checks it with Pillow, and shrinks it to 1568 px at most.
3. `ProductExtractService` sends the image, the category list and known brands to Claude, asking for JSON matching a schema.
4. `ClaudeClient` validates the answer with `ExtractedProductSerializer`, retrying once if it's invalid.
5. The form fills in with badges. Nothing is saved until the user clicks **Add product**.

### Natural-language search
1. `AskAiPanel` sends the sentence to `POST /api/ai/parse-search/`.
2. `NLSearchService` asks Haiku for filters. Brand, category and ordering are `enum`s in the schema, built from the real catalog.
3. `ParsedSearchSerializer` is the whitelist: unknown values are dropped.
4. `_drop_words_that_find_nothing` removes stray search words such as "packets", when something else was understood.
5. The filters go into the URL, and the normal product list does the search. Identical queries are cached for 10 minutes.

### Look-alike detector
1. On save, `analyze_product` calls `LookalikeService.analyze`. It only redoes what changed: the image, the text, or neither.
2. `ImageService.measure` computes the perceptual hash, size and blur score.
3. `refresh_pairs` compares against products of the same brand and top-level category. **Photos:** the number of differing bits between hashes (Hamming distance), flagged at 10 or fewer of 64. **Text:** `EmbeddingService`, with embeddings at ≥ 0.90 or `pg_trgm` at ≥ 0.50.
4. `differing_attributes` compares pack size and variant. Both filled and different means Distinct; otherwise Unresolved.
5. Decisions by people (`resolved_by` is set) are never overwritten.

## Likely interview questions

**Why Django when you know MERN?**
The brief asked for it, and it's Infilect's stack. The concepts carry over; see the table above. Serializers and migrations were the most useful differences.

**What happens if the LLM returns something wrong or malicious?**
It can only return data. A schema shapes it, a serializer validates it, unknown keys are ignored, and brand and category must exist. It never writes SQL. For photos, a person reviews everything before saving.

**What about text on a pack saying "ignore your instructions"?**
The prompt says packaging text is data. More importantly, even if the model obeyed, the output could only be product fields, and nothing is saved without review. The real protection is the design, not the prompt.

**What is SSRF, and how did you stop it?**
The server fetches URLs that users supply, so someone could point it at internal addresses like the cloud metadata service. `ImageService` allows only http/https, resolves the host, blocks non-public IPs, rechecks each redirect, and limits time and size. One gap remains: the host is resolved again when connecting, so DNS could change in between.

**Why not put the logic in `Model.save()` or in views?**
Service classes can be tested alone and read clearly. Hidden work in `save()` would also run during seeding, which must skip it.

**Why does the seed bypass the API?**
It includes deliberately bad data, such as an invalid GTIN, that the API rejects.

**How do you avoid N+1 queries?**
`select_related` loads the category, its parents and the creator in one query. `CategoryViewSet` annotates a child count instead of querying per category.

**What is a perceptual hash, and how well did it work?**
A 64-bit fingerprint of how an image looks; similar images differ in few bits. Honestly, it only caught a near-identical photo on this data. The closest different pair was 16 bits apart, above the threshold of 10, so names did most of the work.

**Embeddings vs trigrams?**
Embeddings capture meaning, while trigrams compare shared letter groups. Embeddings are better but the model peaked at about 320 MB, so production uses trigrams. I measured this before deciding, and tuned the trigram threshold on real data from 0.60 to 0.50.

**Why is Celery not used in production?**
A worker costs money. `CELERY_TASK_ALWAYS_EAGER` runs the same task inline, at the cost of slower saves.

**How do rate limits work, and what are the weaknesses?**
DRF's `ScopedRateThrottle` counts per user or IP in the cache. On Render, `X-Forwarded-For` can be forged, so `GlobalAiThrottle` adds one shared daily counter to cap AI spend. Counters live in memory, which only suits one process; that's why gunicorn runs 1 worker with threads.

**What about the free-tier cold start?**
Render sleeps after 15 idle minutes, and in practice waking it sometimes hung for hours. I first used a GitHub Actions cron to ping it, but GitHub only ran it every few hours. Now an UptimeRobot monitor pings `/api/health/` every 5 minutes, so the service never sleeps, and I get an email if it goes down. The health endpoint skips the database so Neon can still sleep.

**Name a bug you found and fixed.**
Ask AI sometimes left stray words like "packets left" in the search, and since every word must match, the list came back empty. A better prompt alone wasn't reliable, so the server now drops words that match nothing. Tests with a mocked Claude cover it.

**What would you improve first?**
Host the embedding model so production and local detect alike, add frontend tests, and move rate limits and caching to Redis.

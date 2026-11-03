# ShelfReady — frontend

React 19 + Vite + plain JavaScript. Styling with Tailwind CSS v4, icons from lucide-react,
server state with TanStack Query, routing with React Router.

```bash
nvm use            # Node 22 (see .nvmrc)
cp .env.example .env
npm install
npm run dev        # http://localhost:5173 (expects the API on http://localhost:8000/api)
npm run lint
npm run build
```

## Layout

```
src/
  api/          ApiClient class (axios + JWT refresh interceptor) and one file per API area
  auth/         AuthProvider, useAuth, ProtectedRoute
  components/   ui/ (buttons, fields, modal, toast…), layout/ (sidebar, shell), catalog/ (table, grid, filters…)
  hooks/        useUrlFilters (filters live in the query string), useProducts, useDebounce…
  lib/          formatting, validation (mirrors the backend rules), ApiError
  pages/        one component per route
```

Design direction: white canvas, hairline borders, Inter, one blue accent, status colour only as
dots and chips. Every data screen has loading (skeleton), empty and error (retry) states.

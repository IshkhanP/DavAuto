# BlackSharkCars

A premium full-stack automotive marketplace — React + TypeScript frontend, FastAPI + SQLAlchemy 2 + PostgreSQL backend, with a one-shot automation script that bootstraps everything from a clean machine.

```
blacksharkcars/
├── backend/          # FastAPI + SQLAlchemy 2 + PostgreSQL
├── frontend/         # React 18 + Vite + TypeScript
├── docker/           # Dockerfiles for both services
├── docker-compose.yml
├── run.py            # ONE-SHOT automation: DB → venv → migrations → tests → servers
├── run.bat / run.sh  # Convenience wrappers for run.py
├── .env.example
└── README.md
```

---

## 1. Quick start — automated (recommended)

The `run.py` script is the **single entry point**. It:

1. Checks that `python`, `psql`, `node`, `npm` (or `docker`) are installed.
2. Creates the `blacksharkcars` PostgreSQL database if it doesn't exist (using standard `postgres:postgres` credentials).
3. Creates a project-local `.venv` at `backend/.venv` and installs requirements.
4. Runs `alembic upgrade head` (creates the schema).
5. Runs the seed script (demo users, cars, makes, models, locations, etc.).
6. Runs backend tests (`pytest -q`) and frontend tests (`vitest --run`).
7. Starts `uvicorn` (port `8000`) and `vite` (port `5173`) and streams their logs.
8. Press `Ctrl+C` to stop both processes cleanly.

### Windows

```powershell
cd C:\Users\user\Desktop\DavAuto
python run.py
# or, if you have a psql/Postgres installed already:
run.bat             # interactive
run.bat local       # local mode (no Docker)
run.bat docker      # Docker mode
run.bat tests       # only run tests
```

### macOS / Linux

```bash
cd ~/DavAuto
python3 run.py
# or
./run.sh local
./run.sh docker
./run.sh tests
```

### Non-interactive flags

```bash
python run.py --local        # local mode, no prompt
python run.py --docker       # Docker mode, no prompt
python run.py --tests        # only run tests, skip starting servers
python run.py --no-tests     # skip tests, just start the servers
```

When asked, the default selection is `local` (just press Enter).

---

## 2. Manual installation (step by step)

If you prefer to do it yourself — or if `run.py` doesn't work in your environment — follow these steps.

### 2.1 Prerequisites

| Tool        | Min version | Notes                                                        |
|-------------|-------------|--------------------------------------------------------------|
| Python      | 3.12+       | Add to PATH on Windows.                                      |
| Node.js     | 18+         | Includes npm.                                                |
| PostgreSQL  | 14+         | Default `postgres` user with password `postgres` is expected. |
| `psql`      | any         | Optional, only needed by the automation script.              |
| Git         | any         | For cloning the repo.                                        |
| Docker      | optional    | Only required for `--docker` mode.                            |

You can verify everything is present:

```powershell
python --version
node --version
psql --version
```

### 2.2 Clone and configure

```bash
git clone <your-repo-url> blacksharkcars
cd blacksharkcars
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

Open `backend/.env` and **change `JWT_SECRET_KEY` and `JWT_REFRESH_SECRET_KEY`** to long random strings.

### 2.3 Start PostgreSQL

The defaults assume a local Postgres on `localhost:5432` with `postgres:postgres`.

#### Option A — Docker (simplest)

```bash
docker run -d --name bsc-postgres -p 5432:5432 \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=blacksharkcars \
  postgres:16-alpine
```

#### Option B — Native install

If you already have PostgreSQL installed, just make sure the `postgres` role has password `postgres`:

```sql
-- in psql as a superuser
ALTER USER postgres WITH PASSWORD 'postgres';
```

Then create the database:

```bash
# Windows
psql -U postgres -h localhost -c "CREATE DATABASE blacksharkcars;"
# macOS / Linux (if peer auth is enabled, omit -U)
psql -U postgres -c "CREATE DATABASE blacksharkcars;"
```

### 2.4 Backend setup with `.venv`

The recommended way to run the backend is in an **isolated virtual environment** so its dependencies don't pollute your system Python.

#### Create and activate the venv

**Windows (PowerShell):**
```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks the activation script (`execution policy` error), run once:
```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

Then activate again with `.\.venv\Scripts\Activate.ps1`. Your prompt will be prefixed with `(.venv)`.

**Windows (cmd.exe):**
```cmd
cd backend
python -m venv .venv
.venv\Scripts\activate.bat
```

**macOS / Linux:**
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
```

#### Install dependencies

With the venv **activated**:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

If you want to use a specific Python version on macOS / Linux:
```bash
python3.12 -m venv .venv
```

#### Verify the install

```bash
python -c "import fastapi, sqlalchemy, alembic, jose, passlib, bcrypt, psycopg2, pydantic; print('OK')"
```

You should see `OK`.

#### Apply migrations

```bash
alembic upgrade head
```

This creates all 31 tables in the `blacksharkcars` database.

#### Seed demo data

```bash
python -m scripts.seed
```

This inserts categories, makes, models, locations, demo users, a demo dealer, and 16 sample cars.

#### Run the backend

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Open <http://127.0.0.1:8000/docs> to see the interactive Swagger UI.

#### Run backend tests

```bash
pytest -q
```

The first run will create a separate `blacksharkcars_test` database, run all tests against it, then drop it.

### 2.5 Frontend setup

```bash
cd ../frontend
npm install
npm run dev
```

Open <http://127.0.0.1:5173>. The frontend dev server proxies `/api/*` to the backend on port `8000`.

#### Run frontend tests

```bash
npm run test -- --run
```

---

## 3. Production build (frontend)

```bash
cd frontend
npm run build
```

Outputs a static bundle in `frontend/dist/`. Serve it with any static file server (nginx, Caddy, etc.) and point the backend's `CORS_ORIGINS` at the production domain.

---

## 4. Docker mode (one container per service)

```bash
docker-compose up --build
```

This brings up:
- `bsc_postgres` — PostgreSQL 16
- `bsc_backend` — FastAPI on port `8000` (auto-runs migrations + seed on first start)
- `bsc_frontend` — Vite dev server on port `5173`

Stop with `Ctrl+C` or `docker-compose down`. To start fresh (drops the DB too), use `docker-compose down -v`.

---

## 5. Default development credentials

| Role        | Email                              | Password        |
|-------------|------------------------------------|-----------------|
| Super Admin | admin@blacksharkcars.local         | `ChangeMe!2025` |
| User        | user@blacksharkcars.local          | `Demo!2025`     |
| Seller      | seller@blacksharkcars.local        | `Demo!2025`     |
| Dealer      | dealer@blacksharkcars.local        | `Demo!2025`     |

**Change every one of these before deploying to production.**

---

## 6. Project layout

```
blacksharkcars/
├── backend/
│   ├── app/
│   │   ├── api/v1/         # FastAPI routers (auth, cars, admin, super-admin, ...)
│   │   ├── core/            # config, database, security (JWT, bcrypt)
│   │   ├── models/          # SQLAlchemy 2 ORM models
│   │   ├── schemas/         # Pydantic request/response models
│   │   ├── services/        # audit, email, notifications, storage
│   │   ├── repositories/    # DB query layer (e.g. car_repository)
│   │   ├── permissions/     # RBAC: PermissionCodes, get_current_user, require_permission
│   │   ├── middleware/      # Security headers
│   │   ├── utils/           # slugify, etc.
│   │   └── main.py          # FastAPI app + lifespan
│   ├── alembic/            # migrations
│   │   ├── versions/0001_initial.py
│   │   └── env.py
│   ├── scripts/seed.py     # demo data
│   ├── tests/              # pytest
│   ├── .env.example
│   ├── alembic.ini
│   ├── requirements.txt
│   └── pytest.ini
│
├── frontend/
│   ├── src/
│   │   ├── components/      # CarCard, FilterSidebar, HeroSearch, ...
│   │   ├── context/         # AuthContext
│   │   ├── hooks/           # useAsync
│   │   ├── layouts/         # PublicLayout, DashboardLayout, AdminLayout, SuperAdminLayout
│   │   ├── pages/           # HomePage, SearchPage, CarDetailPage, dashboard/, admin/, superadmin/
│   │   ├── router/          # AppRouter, ProtectedRoute, AdminRoute, SuperAdminRoute
│   │   ├── services/        # api client, typed service helpers
│   │   ├── styles/          # globals.css (design system)
│   │   ├── types/           # TypeScript types
│   │   ├── utils/           # format helpers
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── public/
│   ├── index.html
│   ├── package.json
│   ├── tsconfig.json
│   └── vite.config.ts
│
├── docker/
│   ├── backend.Dockerfile
│   └── frontend.Dockerfile
│
├── docker-compose.yml
├── run.py                   # ← the automation script
├── run.bat
├── run.sh
├── .env.example
├── .dockerignore
├── .gitignore
└── README.md
```

---

## 7. Architecture overview

### Backend (FastAPI + SQLAlchemy 2)

- **Versioned REST API** at `/api/v1/*` (Swagger UI at `/docs`, ReDoc at `/redoc`)
- **SQLAlchemy 2.x** ORM with **Alembic** migrations — the schema is fully normalized with proper foreign keys, indexes, and constraints
- **PostgreSQL** primary store (works on 14+)
- **JWT auth**: access token (30 min) + refresh token (14 days) with rotation, revocation, and `jti` tracking in the DB
- **bcrypt** password hashing (12 rounds)
- **Storage abstraction** — `local` filesystem in dev, S3-compatible in prod. The DB stores only URLs / keys.
- **DB-backed RBAC** — every endpoint checks permissions against the database. `PermissionCodes` lives in `app/permissions/definitions.py` and is seeded on startup.
- **Audit logs** for every privileged action (admin moderation, super-admin changes, login events, etc.)
- **File-upload validation** (content-type, size, image dimensions)
- **Account lockout** after 10 failed login attempts (30-minute cooldown)
- **Token refresh interceptor** on the frontend

### Frontend (React 18 + Vite + TypeScript)

- **React Router** with role-aware route guards (`<ProtectedRoute>`, `<AdminRoute>`, `<SuperAdminRoute>`) — these are UX only; the backend enforces everything independently
- **Axios** client with automatic token refresh on `401`
- **`react-hot-toast`** for non-blocking notifications
- **Modular layouts** — `PublicLayout`, `DashboardLayout`, `AdminLayout` (dark sidebar), `SuperAdminLayout` (control center)
- **Reusable components** — `CarCard`, `FilterSidebar`, `HeroSearch`, `Header`, `Footer`, `Pagination`, `CarCardSkeleton`, `EmptyState`, `ErrorState`, `LoadingBlock`
- **Responsive** — mobile-first layouts throughout
- **Loading / empty / error states** on every major page
- **JWT tokens** stored in `localStorage`

### Security principles

- **Backend derives identity from JWT, never from frontend claims.** `role`, `user_id`, `seller_id`, `permissions` are all looked up from the DB on every request.
- **Permission codes** are stored in the database and granted through role assignments. They are NOT hard-coded in React.
- **Admins cannot grant `SUPER_ADMIN`** — only a super admin can. The endpoint explicitly rejects `role_id: SUPER_ADMIN` for non-super-admin callers.
- **All file uploads** check `content-type` and `size`; dimensions are validated on the backend.
- **Audit logs** are append-only; super admins can review them.
- **CORS** is restricted to the configured `CORS_ORIGINS` in `backend/.env`.

---

## 8. API reference (high level)

All under `/api/v1`:

| Endpoint                                 | Method | Auth         | Description                          |
|------------------------------------------|--------|--------------|--------------------------------------|
| `/auth/register`                          | POST   | —            | Create a new user account            |
| `/auth/login`                             | POST   | —            | Get access + refresh tokens          |
| `/auth/refresh`                           | POST   | —            | Rotate refresh token                  |
| `/auth/logout`                            | POST   | refresh      | Revoke the supplied refresh token    |
| `/auth/logout-all`                        | POST   | bearer       | Revoke every refresh token            |
| `/auth/forgot-password`                   | POST   | —            | Request a password-reset email        |
| `/auth/reset-password`                    | POST   | token        | Submit a new password using a token  |
| `/auth/verify-email`                      | POST   | token        | Verify the email address              |
| `/auth/me`                                | GET    | bearer       | Get the current user                  |
| `/auth/me`                                | PATCH  | bearer       | Update the current user profile       |
| `/auth/change-password`                   | POST   | bearer       | Change the current password          |
| `/cars`                                   | GET    | —            | Public search (filters, pagination)  |
| `/cars/featured`                          | GET    | —            | Featured listings                     |
| `/cars/latest`                            | GET    | —            | Newest listings                       |
| `/cars/similar/{car_id}`                 | GET    | —            | Similar cars                          |
| `/cars/{id}`                              | GET    | —            | Listing details (with view increment) |
| `/cars`                                   | POST   | bearer       | Create a new listing                  |
| `/cars/{id}`                              | PATCH  | owner/admin  | Update a listing                      |
| `/cars/{id}/status`                       | POST   | owner/admin  | Change listing status                |
| `/cars/{id}/duplicate`                    | POST   | owner        | Duplicate a listing as a draft       |
| `/cars/{id}`                              | DELETE | owner/admin  | Delete (soft) a listing               |
| `/cars/mine/all`                          | GET    | bearer       | Current user's listings              |
| `/favorites`                              | GET    | bearer       | Current user's favorites             |
| `/favorites/{car_id}`                     | POST   | bearer       | Add a favorite (idempotent)           |
| `/favorites/{car_id}`                     | DELETE | bearer       | Remove a favorite                     |
| `/conversations`                          | GET/POST | bearer     | List or open a conversation         |
| `/conversations/{id}`                     | GET    | participant  | Read a conversation                  |
| `/conversations/{id}/messages`            | GET/POST | participant | List or send messages                |
| `/conversations/{id}/read`                | POST   | participant  | Mark a conversation as read          |
| `/notifications`                          | GET    | bearer       | Current user's notifications         |
| `/notifications/unread-count`             | GET    | bearer       | Unread count                          |
| `/catalog/categories` / `makes` / `locations` | GET | — | Public catalog data                |
| `/dealers`                                | GET/POST | bearer     | Public list / authenticated create   |
| `/dealers/{id}`                           | GET    | —            | Dealer details                        |
| `/admin/stats`                            | GET    | permission   | Admin dashboard stats                 |
| `/admin/listings`                         | GET    | permission   | List all listings                     |
| `/admin/listings/{id}/approve`            | PATCH  | permission   | Approve a listing                     |
| `/admin/listings/{id}/reject`             | PATCH  | permission   | Reject a listing                      |
| `/admin/listings/{id}/feature`            | PATCH  | permission   | Toggle featured                       |
| `/admin/listings/bulk-action`             | POST   | permission   | Bulk approve / reject / feature / delete |
| `/admin/reports`                          | GET    | permission   | List user reports                     |
| `/admin/reports/{id}/resolve`             | POST   | permission   | Resolve a report                      |
| `/admin/users`                            | GET    | permission   | List users                            |
| `/admin/users/{id}`                       | PATCH  | permission   | Update / suspend / restore            |
| `/super-admin/*`                          | —      | SUPER_ADMIN  | Roles, permissions, settings, audit log, etc. |

---

## 9. Database schema (31 tables)

Key tables: `users`, `roles`, `permissions`, `user_roles`, `role_permissions`, `refresh_tokens`, `password_reset_tokens`, `email_verification_tokens`, `cars`, `car_images`, `car_videos`, `car_features`, `favorites`, `conversations`, `conversation_participants`, `messages`, `notifications`, `dealers`, `dealer_employees`, `categories`, `makes`, `models`, `locations`, `reports`, `promotion_packages`, `user_promotions`, `payments`, `reviews`, `audit_logs`, `site_settings`.

All tables use **UUID primary keys** (via `gen_random_uuid()`), `created_at` / `updated_at` timestamps, and **strategic indexes** for the most-queried columns (`price`, `year`, `mileage`, `make_id`, `model_id`, `status`, `published_at`, `is_featured`, `is_promoted`).

---

## 10. Logging & error tracking

The backend writes all logs to **both stdout** and a **rotating log file** at:

```
backend/logs/blacksharkcars.log
```

- **Rotation**: 5 MB per file, 5 backups kept
- **Format**: `2026-09-03T15:00:47+0400 [LEVEL] logger: message`
- **What gets logged**:
  - Every unhandled exception with full traceback (`logger.exception`)
  - Every Pydantic request-validation error with the URL and detailed errors (`logger.warning`)
  - All startup / bootstrap events (`logger.info`)
  - Uncaught exceptions via `sys.excepthook`

To watch logs in real time while the server is running:

```bash
# Windows PowerShell
Get-Content backend\logs\blacksharkcars.log -Wait

# macOS / Linux
tail -f backend/logs/blacksharkcars.log
```

The `backend/logs/` directory is git-ignored, so logs stay local.

---

## 11. Troubleshooting

### `psql: error: connection to server at "localhost" failed: password authentication failed`

`psql` defaults to the OS user (`user`), but the `postgres` role needs the `postgres` password. The `run.py` script always passes `-U postgres` explicitly, but for manual `psql` calls you need to do the same:

```bash
psql -U postgres -h localhost -d blacksharkcars
# set PGPASSWORD=postgres first to avoid the interactive prompt
```

### `JWT_ALGORITHM=HS256$env:PGPASSWORD = "postgres"`

This is **not a bug in the code** — it's PowerShell variable interpolation leaking into the file. When you run commands like `python -m scripts.seed > backend/.env` from PowerShell, the shell may expand `$env:PGPASSWORD` into the file. **Always use `Edit` or a real text editor to write the `.env` file**, or use:

```powershell
'JWT_ALGORITHM=HS256' | Add-Content backend/.env
```

The shipped `backend/.env.example` is correct.

### "Error: PydanticUndefinedAnnotation: name 'Request' is not defined"

If you hit this on startup, make sure every router imports `Request` from `fastapi`. This is fixed in the current code; the error usually means you edited a file and removed the import.

### Backend tests fail with "DuplicateTable: relation '...' already exists"

The pytest fixture uses a separate `blacksharkcars_test` database. If you see this error, drop the test database manually:

```bash
psql -U postgres -c "DROP DATABASE IF EXISTS blacksharkcars_test;"
```

Then re-run the tests. The fixture will recreate the DB.

### Frontend shows a black page

Open the browser console (F12) — most likely a JS error or a 502 from the backend. Make sure:

1. The backend is running on port `8000` (visit `http://127.0.0.1:8000/docs`)
2. CORS is configured to allow `http://localhost:5173` in `backend/.env`
3. You are logged in (token in `localStorage`)

### "Address already in use" on port 8000 or 5173

Another process is using the port. Find and stop it:

```bash
# Windows
netstat -ano | findstr ":8000"
taskkill /PID <pid> /F
# macOS / Linux
lsof -i :8000
kill <pid>
```

### `pip install` hangs or times out in the script

If your network can't reach PyPI, `run.py` will fail after 5 minutes with a clear error. To work around, pre-install the requirements outside the script:

```bash
cd backend
python -m pip install -r requirements.txt
python run.py
```

`run.py` will detect the already-installed packages and skip pip.

### Sandbox / antivirus blocks esbuild during frontend tests

You may see an `EPERM` error from `npm run test`. This is a sandbox issue, not a code issue. The application still runs fine — the test runner is what's blocked. On a normal machine, vitest will work.

---

## 12. License

Proprietary. © BlackSharkCars.

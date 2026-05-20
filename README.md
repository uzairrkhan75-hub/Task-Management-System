# Drivex Auto Repair Shop Management

Drivex is a Django-based auto repair shop management system for tracking cars, mechanics, and repair tasks in one place.

## Overview

The application supports the full repair workflow: vehicle intake, mechanic assignment, task creation, and repair status tracking. Two roles are supported — **Manager** (full access) and **Mechanic** (own tasks only).

## Features

- Car management: create, update, list, and delete car records
- Mechanic management: store mechanic details, specialization, and availability
- Task management: assign repair tasks to cars and mechanics with ETA auto-calculation
- Inline status and priority updates on the task list
- Customer-facing car ETA lookup page
- Role-based access control (Manager / Mechanic)
- Dark/light theme toggle (site and admin)
- Jazzmin admin dashboard with custom theme styling

## Technology Stack

- Django 6
- SQLite locally; PostgreSQL in production (`DATABASE_URL`)
- WhiteNoise for static files in production; Docker Compose for local containers
- Bootstrap 5 + Bootswatch (Cyborg dark / Flatly light)
- Django Jazzmin admin theme
- Font Awesome icons

## Project Structure

```text
Task_Managment_system/
  manage.py
  db.sqlite3
  task/
    settings/
    urls.py
    wsgi.py
    asgi.py
  taskapp/
    models.py
    views.py
    urls.py
    admin.py
    forms.py
    rbac.py
    mixins.py
    context_processors.py
    tests.py
    templatetags/
    templates/
    static/
```

## Installation

1. Create and activate a virtual environment:

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # macOS / Linux
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Apply migrations:

```bash
python manage.py migrate
```

4. Create an admin user:

```bash
python manage.py createsuperuser
```

5. Create the **Manager** group in Django admin (`/admin/auth/group/add/`) and assign users to it for manager-level shop access.

6. Run the development server:

```bash
python manage.py runserver
```

Settings modules:

- **`task.settings`** (default via `manage.py` / `wsgi.py`): local development (`SQLite`, `DEBUG=True`).
- **`task.settings.production`**: PostgreSQL (`DATABASE_URL`), WhiteNoise compressed static files, HTTPS-oriented cookies (`SECURE_SSL_REDIRECT` defaults to true).

Optional: silence WhiteNoise locally by running **`python manage.py collectstatic`** once (creates `staticfiles/`). Production Docker images run **`collectstatic`** during the image build.

## Production, Docker & CI/CD

### Environment variables (`task.settings.production`)

| Variable | Required | Notes |
|----------|----------|--------|
| `SECRET_KEY` | Yes | Strong random secret |
| `DATABASE_URL` | Yes | Postgres URL (e.g. from Render Postgres) |
| `ALLOWED_HOSTS` | Yes | Comma-separated hostnames (`your-app.onrender.com`) |
| `CSRF_TRUSTED_ORIGINS` | Yes | Comma-separated origins (`https://your-app.onrender.com`) |
| `SECURE_SSL_REDIRECT` | No | Default `true`; set `false` only for plain HTTP (e.g. local Docker over HTTP) |

### Docker Compose (Postgres + web)

```bash
docker compose up --build
```

Open `http://localhost:8000`. The stack uses `task.settings.production` with `SECURE_SSL_REDIRECT=false` and HTTP CSRF origins for local convenience.

### Render

1. Create a **PostgreSQL** instance (or apply `render.yaml` and fill in secrets in the dashboard).
2. Create a **Web Service** using this repo’s **`Dockerfile`**, or connect the blueprint.
3. Set **`DJANGO_SETTINGS_MODULE`** = `task.settings.production` (already the default inside the Docker image).
4. Set **`SECRET_KEY`**, **`ALLOWED_HOSTS`**, **`CSRF_TRUSTED_ORIGINS`**, and attach **`DATABASE_URL`** to the Postgres service.

Copy **Deploy Hook** URL from Render (Dashboard → Service → Settings → Deploy Hook).

### GitHub Actions

Workflow: `.github/workflows/ci.yml`.

- On every PR and push: installs dependencies, runs `manage.py check` and **`python manage.py test`** with **`task.settings.development`** (SQLite).
- On push to **`main`** or **`master`**: posts to **`RENDER_DEPLOY_HOOK_URL`** if that repository secret is set; otherwise the deploy step is skipped.

Add the secret in **GitHub → Settings → Secrets and variables → Actions** → `RENDER_DEPLOY_HOOK_URL`.

## Usage

- Site: `http://127.0.0.1:8000/`
- Admin: `http://127.0.0.1:8000/admin/`

## Database Models

### Mechanic

| Field | Description |
|---|---|
| `name` | Full name |
| `specialization` | Area of expertise |
| `phone_number` | Contact number |
| `is_active` | Active flag |
| `is_on_leave` | Marks unavailability |
| `is_manually_busy` | Override busy state without an open task |
| `user` | Optional linked login (OneToOne) |

Properties: `is_busy`, `is_effectively_busy`, `availability_status`, `availability_label`

### Car

| Field | Description |
|---|---|
| `registration_number` | Unique plate number |
| `make` / `model` / `year` | Vehicle details |
| `customer_name` / `customer_phone` | Owner info |
| `status` | `waiting` → `assigned` → `in_progress` → `completed` |

Property: `repair_eta` — earliest `promised_completion_at` of open tasks

### Task

| Field | Description |
|---|---|
| `car` | FK to Car |
| `mechanic` | FK to Mechanic (nullable) |
| `title` / `description` | Task details |
| `status` | `pending` / `in_progress` / `completed` |
| `priority` | `low` / `medium` / `high` |
| `estimated_hours` | Used to auto-calculate `promised_completion_at` on save |
| `promised_completion_at` | Set automatically from `created_at + estimated_hours` |

Property: `is_overdue`

## URL Reference

```
/                          Manager dashboard
/accounts/login/           Login
/accounts/logout/          Logout
/track-car/                Public customer ETA lookup
/cars/                     Car list
/cars/create/
/cars/<pk>/update/
/cars/<pk>/delete/
/mechanics/                Mechanic list
/mechanics/create/
/mechanics/<pk>/update/
/mechanics/<pk>/delete/
/mechanics/<pk>/availability/
/tasks/                    Task list
/tasks/create/
/tasks/<pk>/update/
/tasks/<pk>/delete/
/tasks/<pk>/set-status/
/tasks/<pk>/set-priority/
/users/                    User list (manager only)
/users/create/
/users/<pk>/update/
/users/<pk>/delete/
/admin/                    Jazzmin admin
```

## Role-Based Access

| Role | Who | Access |
|---|---|---|
| `manager` | Superuser or member of `Manager` group | Full shop UI |
| `mechanic` | User linked via `Mechanic.user` | Own tasks only |
| none | Everyone else | Redirected to login |

---

## Testing

The test suite lives in `taskapp/tests.py` and covers 84 automated tests across models, RBAC, views, CRUD, and inline actions.

### Run all tests

```bash
python manage.py test taskapp
```

### Run a specific class

```bash
python manage.py test taskapp.tests.TaskModelTest
python manage.py test taskapp.tests.RBACTest
python manage.py test taskapp.tests.AccessControlTest
```

### Run with full output

```bash
python manage.py test taskapp --verbosity=2
```

### Test coverage

| Test class | Count | What it covers |
|---|---|---|
| `MechanicModelTest` | 8 | `is_busy`, `availability_status`, on-leave priority, `__str__` |
| `CarsModelTest` | 5 | `repair_eta` — no tasks, soonest ETA, ignores completed/no-ETA tasks |
| `TaskModelTest` | 9 | ETA auto-calc, ETA clear on hours removal, `is_overdue`, clears `is_manually_busy` on assignment |
| `RBACTest` | 10 | `is_shop_manager`, `resolve_shop_access_role`, `get_mechanic_profile`, task queryset scoping |
| `AuthViewTest` | 6 | Login page loads, correct redirect per role, bad credentials rejected, logout |
| `AccessControlTest` | 8 | Manager-only pages blocked for mechanics, mechanic task list allowed, track-car blocked |
| `CarCRUDTest` | 6 | List, create, duplicate registration rejected, update, delete, task cascade delete |
| `MechanicCRUDTest` | 4 | List, create, update, delete |
| `MechanicAvailabilityTest` | 5 | On leave, manually busy, free, free blocked with open tasks, mechanic gets 403 |
| `TaskCRUDTest` | 5 | List, create, create with ETA, update, delete |
| `TaskInlineActionsTest` | 7 | Manager sets status/priority, assigned mechanic changes status, unassigned gets 403, invalid value rejected, GET blocked |
| `CustomerEtaTest` | 4 | Car found, case-insensitive search, not found, blank search |
| `DashboardTest` | 4 | Active task count, overdue count, due-soon count, total cars |

### Important notes for writing additional tests

- **`Task.save()` always recomputes `promised_completion_at`** from `estimated_hours`. You cannot manually set the field via `save()`. Use `Task.objects.filter(pk=...).update(promised_completion_at=...)` to bypass this in tests.
- **`ShopManagerRequiredMixin` redirects mechanics to `/tasks/`** (302), it does not return a 403.
- **`Mechanic.is_busy` is a live DB property** — it queries the database on every access, so `refresh_from_db()` is not needed to pick up changes.

---

## Notes

- The project folder is named `Task_Managment_system` (intentional typo — do not rename).
- SQLite `db.sqlite3` is not committed to git.
- After any model change run `python manage.py makemigrations && python manage.py migrate`.
- The `Manager` group must be created manually in Django admin before any manager logins work.
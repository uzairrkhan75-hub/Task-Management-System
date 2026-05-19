# Drivex — Project Guide for AI Assistants

This file is read automatically by Claude Code at the start of every session. Read it fully before making any changes.

---

## What This Project Is

**Drivex** is a Django web app for managing an auto repair shop. It tracks cars, mechanics, and repair tasks through a full workflow: intake → assignment → task creation → completion.

- **Site UI**: Bootstrap 5 + Bootswatch (Cyborg dark / Flatly light) via cookie-driven theme
- **Admin UI**: Django Jazzmin with a custom dark/light theme toggle (CSS + JS injected at runtime)
- **Auth**: Login required for all shop views; two roles — Manager and Mechanic

---

## Project Layout

```
Task_Managment_system/       ← repo root (folder name has a typo, do not rename)
  manage.py
  task/                      ← Django project config
    settings.py
    urls.py
  taskapp/                   ← single Django app (all models, views, URLs)
    models.py
    views.py
    urls.py
    admin.py
    forms.py
    rbac.py                  ← role helpers (Manager / Mechanic logic)
    mixins.py                ← ShopAccessMixin, ShopManagerRequiredMixin
    context_processors.py   ← injects shop_role, task summary, theme vars
    templatetags/shop_extras.py
    templates/
      base.html              ← site layout (Bootstrap navbar, theme link)
      home.html              ← manager dashboard (ETA card, stats)
      registration/login.html
      cars/ mechanics/ tasks/
    static/taskapp/
      css/admin-dark.css     ← Jazzmin custom CSS (dark + light theme vars)
      css/site-theme.css     ← site-wide navbar / button overrides
      js/admin-theme-toggle.js  ← injects toggle HTML + styles into Jazzmin navbar
      img/admin-logo.svg     ← Drivex "D" logo (SVG path, no text elements)
```

---

## Models

### `Mechanic`
- `name`, `specialization`, `phone_number`, `is_active`
- `is_on_leave` — marks unavailability
- `is_manually_busy` — override busy state without an open task
- `user` (OneToOne → AUTH_USER_MODEL, optional) — links a login to this mechanic
- Properties: `is_busy`, `is_effectively_busy`, `availability_status`, `availability_label`

### `Cars`
- `registration_number` (unique), `make`, `model`, `year`
- `customer_name`, `customer_phone`
- `status`: `waiting` → `assigned` → `in_progress` → `completed`
- Property: `repair_eta` — returns the earliest `promised_completion_at` of open tasks

### `Task`
- `car` (FK → Cars), `mechanic` (FK → Mechanic, nullable)
- `title`, `description`, `status` (pending/in_progress/completed), `priority` (low/medium/high)
- `estimated_hours` — when saved, auto-calculates `promised_completion_at`
- `promised_completion_at` — set automatically from `created_at + estimated_hours`
- `save()` also clears `mechanic.is_manually_busy` when a task is assigned
- Property: `is_overdue`

---

## RBAC (Role-Based Access)

Defined in `taskapp/rbac.py`. Two roles in the shop UI (separate from Django admin permissions):

| Role | Who | Access |
|------|-----|--------|
| `manager` | superuser or member of `Manager` group | full shop UI |
| `mechanic` | user linked via `Mechanic.user` | own tasks only, redirected to task list on login |
| `None` | everyone else | `PermissionDenied` |

- `ShopAccessMixin` — requires manager or mechanic
- `ShopManagerRequiredMixin` — requires manager only

---

## URL Structure

```
/                          home (manager dashboard)
/accounts/login/           ShopLoginView
/accounts/logout/
/track-car/                public customer ETA lookup
/cars/                     CarListView
/cars/create/
/cars/<pk>/update/
/cars/<pk>/delete/
/mechanics/                MechanicListView
/mechanics/create/
/mechanics/<pk>/update/
/mechanics/<pk>/delete/
/mechanics/<pk>/availability/   toggle availability (POST)
/tasks/                    TaskListView
/tasks/create/
/tasks/<pk>/update/
/tasks/<pk>/delete/
/tasks/<pk>/set-status/    AJAX-style status toggle (POST)
/tasks/<pk>/set-priority/  AJAX-style priority toggle (POST)
/users/                    ShopUserListView (manager only)
/users/create/
/users/<pk>/update/
/users/<pk>/delete/
/admin/                    Jazzmin admin
```

---

## Theme System

### Admin (Jazzmin)
- `admin-dark.css` — loaded via `JAZZMIN_SETTINGS["custom_css"]`; defines CSS vars for dark/light on `body[data-dashboard-theme]`
- `admin-theme-toggle.js` — loaded via `JAZZMIN_SETTINGS["custom_js"]`; **injects a `<style>` tag at runtime** (critical — this is how toggle CSS reliably overrides AdminLTE); also injects toggle HTML into `#jazzy-navbar .navbar-nav.ml-auto`
- Theme stored in `localStorage` key `taskapp-admin-theme`

### Site (non-admin pages)
- Bootswatch CDN URLs are injected by `context_processors.site_shop_theme` from a cookie (`drivex_site_theme`)
- Default theme: dark (Cyborg)

---

## Key Conventions

- **Always use `!important`** when overriding AdminLTE/Bootstrap styles in the admin CSS — AdminLTE loads after `custom_css` and will win otherwise
- **Prefer JS-injected `<style>` tags** over `admin-dark.css` for toggle-related styles — the JS `<style>` is appended to `<head>` at runtime and reliably wins specificity battles
- The `taskapp` app name and `task` config folder name are intentional — do not rename them even though the display name is Drivex
- The repo folder is named `Task_Managment_system` (typo: Managment) — do not rename it
- Migrations live in `taskapp/migrations/` — always run `python manage.py migrate` after model changes
- SQLite database (`db.sqlite3`) — not committed to git

---

## Running the Project

```bash
# Activate venv
.venv\Scripts\activate        # Windows

# Run dev server
python manage.py runserver

# After model changes
python manage.py makemigrations
python manage.py migrate

# Create admin user (first time)
python manage.py createsuperuser
```

- Site: http://127.0.0.1:8000/
- Admin: http://127.0.0.1:8000/admin/

---

## Known Quirks

- The `overflow-x: hidden !important` rule on `*` in `admin-dark.css` hides the horizontal scrollbar globally — intended
- The admin logo (`admin-logo.svg`) uses SVG `<path>` with `fill-rule="evenodd"` for the "D" shape — no `<text>` elements (font rendering in SVG-as-img is unreliable)
- `STATIC_URL = 'static/'` (no leading slash) — valid in Django 4+; `{% static %}` template tag resolves it correctly
- The `Manager` group must be created manually in Django admin and users assigned to it for manager access
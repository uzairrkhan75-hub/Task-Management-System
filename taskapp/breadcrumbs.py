"""
URL-name → breadcrumb trail for authenticated shop roles (Bootstrap `breadcrumb`).
"""

from django.urls import reverse
from django.utils.translation import gettext as _

from .rbac import resolve_shop_access_role


def _dashboard():
    """First crumb linking home (manager)."""
    return {"label": _("Dashboard"), "url": reverse("home")}


def _cars_index():
    return {"label": _("Cars"), "url": reverse("car_list")}


def _mechanics_index():
    return {"label": _("Mechanics"), "url": reverse("mechanic_list")}


def _users_index():
    return {"label": _("Users"), "url": reverse("shop_user_list")}


def _tasks_index():
    return {"label": _("Tasks"), "url": reverse("task_list")}


def resolve_shop_breadcrumb_items(request):
    """
    Build list of dicts ``{'label': str, 'url': str | None}``.
    Items with ``url`` link; last item omits ``url`` (current page).
    """
    user = getattr(request, "user", None)
    if not user.is_authenticated:
        return []

    role = resolve_shop_access_role(user)
    if role is None:
        return []

    rm = getattr(request, "resolver_match", None)
    url_name = getattr(rm, "url_name", None) if rm is not None else None
    if not url_name:
        return []

    if rm.app_name == "admin" or (rm.namespaces and "admin" in rm.namespaces):
        return []

    if role == "mechanic":
        # Mechanics primarily use `/tasks/`; task CRUD is manager-only on this codebase.
        if url_name == "task_list":
            return [{"label": _("My tasks"), "url": None}]
        return []

    if role != "manager":
        return []

    # --- Dashboard ---
    if url_name == "home":
        return [{"label": _("Dashboard"), "url": None}]

    if url_name == "customer_eta":
        return [_dashboard(), {"label": _("Track Car"), "url": None}]

    # --- Cars ---
    if url_name == "car_list":
        return [_dashboard(), {"label": _("Cars"), "url": None}]

    if url_name == "car_create":
        return [_dashboard(), _cars_index(), {"label": _("Add car"), "url": None}]

    if url_name == "car_update":
        return [_dashboard(), _cars_index(), {"label": _("Edit car"), "url": None}]

    if url_name == "car_delete":
        return [_dashboard(), _cars_index(), {"label": _("Delete car"), "url": None}]

    # --- Mechanics ---
    if url_name == "mechanic_list":
        return [_dashboard(), {"label": _("Mechanics"), "url": None}]

    if url_name == "mechanic_create":
        return [_dashboard(), _mechanics_index(), {"label": _("Add mechanic"), "url": None}]

    if url_name == "mechanic_update":
        return [_dashboard(), _mechanics_index(), {"label": _("Edit mechanic"), "url": None}]

    if url_name == "mechanic_delete":
        return [_dashboard(), _mechanics_index(), {"label": _("Delete mechanic"), "url": None}]

    # --- Users ---
    if url_name == "shop_user_list":
        return [_dashboard(), {"label": _("Users"), "url": None}]

    if url_name == "shop_user_create":
        return [_dashboard(), _users_index(), {"label": _("Add user"), "url": None}]

    if url_name == "shop_user_update":
        return [_dashboard(), _users_index(), {"label": _("Edit user"), "url": None}]

    if url_name == "shop_user_delete":
        return [_dashboard(), _users_index(), {"label": _("Delete user"), "url": None}]

    # --- Tasks ---
    if url_name == "task_list":
        return [_dashboard(), {"label": _("Tasks"), "url": None}]

    if url_name == "task_create":
        return [_dashboard(), _tasks_index(), {"label": _("Add task"), "url": None}]

    if url_name == "task_update":
        return [_dashboard(), _tasks_index(), {"label": _("Edit task"), "url": None}]

    if url_name == "task_delete":
        return [_dashboard(), _tasks_index(), {"label": _("Delete task"), "url": None}]

    if url_name in ("login", "logout"):
        return []

    return []

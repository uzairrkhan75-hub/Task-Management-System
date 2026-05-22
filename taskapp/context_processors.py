from django.db.models import Count, Q
from django.urls import reverse

from .models import Mechanic, Task
from .rbac import get_mechanic_profile, resolve_shop_access_role
from .breadcrumbs import resolve_shop_breadcrumb_items

# Bootswatch (must match URLs used in templates / theme toggle JS)
SITE_BOOTSWATCH_DARK_CSS = (
    'https://cdn.jsdelivr.net/npm/bootswatch@5.3.3/dist/cyborg/bootstrap.min.css'
)
SITE_BOOTSWATCH_LIGHT_CSS = (
    'https://cdn.jsdelivr.net/npm/bootswatch@5.3.3/dist/flatly/bootstrap.min.css'
)
SITE_THEME_COOKIE = 'drivex_site_theme'


def admin_mechanic_task_summary(request):
    """Populate admin index dashboard widgets (templates/admin/index.html)."""
    try:
        admin_index = reverse('admin:index')
    except Exception:
        return {}

    if request.path.rstrip('/') != admin_index.rstrip('/'):
        return {}

    mechanic_pending_rows = list(
        Mechanic.objects.filter(is_active=True)
        .annotate(
            pending_count=Count('tasks', filter=Q(tasks__status='pending')),
            in_progress_count=Count(
                'tasks',
                filter=Q(tasks__status='in_progress'),
            ),
        )
        .order_by('name'),
    )

    task_totals = {
        'pending': Task.objects.filter(status='pending').count(),
        'in_progress': Task.objects.filter(status='in_progress').count(),
        'open': Task.objects.exclude(status='completed').count(),
    }

    return {
        'mechanic_pending_rows': mechanic_pending_rows,
        'task_totals': task_totals,
    }


def shop_roles(request):
    user = request.user
    role = resolve_shop_access_role(user) if user.is_authenticated else None
    return {
        'shop_role': role,
        'is_shop_manager': role == 'manager',
        'shop_mechanic': get_mechanic_profile(user) if user.is_authenticated else None,
    }


def shop_breadcrumbs(request):
    return {'shop_breadcrumb_items': resolve_shop_breadcrumb_items(request)}


def site_shop_theme(request):
    """
    Initial Bootswatch stylesheet href for base.html.

    Prefer cookie so the first response includes a real <link> (render-blocking),
    avoiding FOUC from JS-injected stylesheets. Client JS reconciles with
    localStorage and refreshes the cookie when they differ.
    """
    raw = request.COOKIES.get(SITE_THEME_COOKIE, '')
    theme = raw if raw in ('light', 'dark') else 'dark'
    return {
        'site_bootswatch_css': (
            SITE_BOOTSWATCH_LIGHT_CSS if theme == 'light' else SITE_BOOTSWATCH_DARK_CSS
        ),
        'site_bootswatch_dark_url': SITE_BOOTSWATCH_DARK_CSS,
        'site_bootswatch_light_url': SITE_BOOTSWATCH_LIGHT_CSS,
        'site_theme_cookie_name': SITE_THEME_COOKIE,
    }

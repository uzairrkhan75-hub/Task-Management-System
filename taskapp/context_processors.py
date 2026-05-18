from django.db.models import Count, Q
from django.urls import reverse

from .models import Mechanic, Task
from .rbac import get_mechanic_profile, resolve_shop_access_role


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

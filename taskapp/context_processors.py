from .rbac import get_mechanic_profile, resolve_shop_access_role


def admin_mechanic_task_summary(request):
    """Reserved for Jazzmin / admin dashboard context (extend as needed)."""
    return {}


def shop_roles(request):
    user = request.user
    role = resolve_shop_access_role(user) if user.is_authenticated else None
    return {
        'shop_role': role,
        'is_shop_manager': role == 'manager',
        'shop_mechanic': get_mechanic_profile(user) if user.is_authenticated else None,
    }

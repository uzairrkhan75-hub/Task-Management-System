"""Role helpers for the shop UI (not Django admin permissions)."""

from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist

# Django auth Group name for shop managers (not superuser).
MANAGER_GROUP = 'Manager'


def is_shop_manager(user) -> bool:
    """Superuser or member of Manager group — full shop UI except Django admin internals."""
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return user.groups.filter(name=MANAGER_GROUP).exists()


def get_mechanic_profile(user):
    """Return the Mechanic linked to this user, or None."""
    if not user.is_authenticated:
        return None
    try:
        return user.mechanic_profile
    except ObjectDoesNotExist:
        return None


def resolve_shop_access_role(user) -> str | None:
    """'manager' | 'mechanic' | None — None means no staff-area access."""
    if not user.is_authenticated:
        return None
    if is_shop_manager(user):
        return 'manager'
    if get_mechanic_profile(user) is not None:
        return 'mechanic'
    return None


def mechanic_tasks_queryset(user):
    from .models import Task

    if not user.is_authenticated:
        return Task.objects.none()
    if is_shop_manager(user):
        return Task.objects.all()
    mech = get_mechanic_profile(user)
    if mech is None:
        return Task.objects.none()
    return Task.objects.filter(mechanic=mech)


def users_available_for_mechanic_link(mechanic_instance):
    """Users not already linked to another Mechanic; keeps current assignment editable."""
    from .models import Mechanic

    User = get_user_model()
    qs = Mechanic.objects.exclude(user=None)
    if mechanic_instance.pk:
        qs = qs.exclude(pk=mechanic_instance.pk)
    taken = qs.values_list('user_id', flat=True)
    available = User.objects.filter(is_active=True).exclude(pk__in=list(taken))
    if mechanic_instance.user_id:
        available = available | User.objects.filter(pk=mechanic_instance.user_id)
    return available.distinct()

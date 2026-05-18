from django import template

from ..rbac import MANAGER_GROUP, get_mechanic_profile

register = template.Library()


@register.inclusion_tag('users/_shop_role_badge.html')
def shop_role_badge(user):
    if user.is_superuser:
        kind = 'superuser'
    elif any(g.name == MANAGER_GROUP for g in user.groups.all()):
        kind = 'manager'
    elif get_mechanic_profile(user) is not None:
        kind = 'mechanic'
    else:
        kind = ''
    return {'kind': kind}

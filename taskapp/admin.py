from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import GroupAdmin as DjangoGroupAdmin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.models import Group
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from .models import Cars, Mechanic, Task
from .rbac import MANAGER_GROUP, get_mechanic_profile

User = get_user_model()
if admin.site.is_registered(User):
    admin.site.unregister(User)

if admin.site.is_registered(Group):
    admin.site.unregister(Group)


@admin.register(Group)
class GroupAdmin(DjangoGroupAdmin):
    """No bulk actions; column headers are plain text (no sort links)."""

    actions = None
    sortable_by = ()


def admin_edit_delete_actions(obj, *, edit_title: str, delete_title: str):
    """Pill Edit / Delete links (styled via admin-dark.css)."""
    opts = obj._meta
    change_url = reverse(
        f'admin:{opts.app_label}_{opts.model_name}_change',
        args=[obj.pk],
    )
    delete_url = reverse(
        f'admin:{opts.app_label}_{opts.model_name}_delete',
        args=[obj.pk],
    )
    return format_html(
        '<div class="admin-row-actions" role="group">'
        '<a class="admin-action-btn admin-action-btn--edit" href="{}" title="{}" aria-label="{}">'
        '<i class="fas fa-edit" aria-hidden="true"></i>'
        '<span class="admin-action-btn__label">{}</span>'
        '</a>'
        '<a class="admin-action-btn admin-action-btn--delete" href="{}" title="{}" aria-label="{}">'
        '<i class="fas fa-trash-alt" aria-hidden="true"></i>'
        '<span class="admin-action-btn__label">{}</span>'
        '</a>'
        '</div>',
        change_url,
        edit_title,
        _('Edit'),
        _('Edit'),
        delete_url,
        delete_title,
        _('Delete'),
        _('Delete'),
    )


@admin.register(Mechanic)
class MechanicAdmin(admin.ModelAdmin):

    list_display = (
        'name',
        'specialization',
        'user',
        'availability_display',
        'on_leave',
        'manual_busy',
        'phone_number',
        'is_active',
        'created_at',
        'admin_actions_display',
    )

    list_filter = (
        'is_active',
        'is_on_leave',
        'is_manually_busy',
        'specialization',
    )

    search_fields = (
        'name',
        'phone_number',
        'specialization',
    )

    ordering = ('name',)

    autocomplete_fields = ('user',)

    @admin.display(boolean=True, description='On leave')
    def on_leave(self, obj):
        return obj.is_on_leave

    @admin.display(boolean=True, description='Manual busy')
    def manual_busy(self, obj):
        return obj.is_manually_busy

    @admin.display(description='Availability')
    def availability_display(self, obj):
        return obj.availability_label

    @admin.display(description=_('Actions'), ordering=False)
    def admin_actions_display(self, obj):
        return admin_edit_delete_actions(
            obj,
            edit_title=_('Edit mechanic "%(name)s"') % {'name': obj.name},
            delete_title=_('Delete mechanic "%(name)s"') % {'name': obj.name},
        )
@admin.register(Cars)
class CarAdmin(admin.ModelAdmin):

    list_display = (
        'registration_number',
        'make',
        'model',
        'customer_name',
        'status',
        'created_at',
        'admin_actions_display',
    )

    list_filter = (
        'status',
        'make',
    )

    search_fields = (
        'registration_number',
        'make',
        'model',
        'customer_name',
    )

    ordering = ('-created_at',)

    @admin.display(description=_('Actions'), ordering=False)
    def admin_actions_display(self, obj):
        return admin_edit_delete_actions(
            obj,
            edit_title=_('Edit car %(reg)s')
            % {'reg': obj.registration_number},
            delete_title=_('Delete car %(reg)s')
            % {'reg': obj.registration_number},
        )


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):

    list_display = (
        'title',
        'car',
        'mechanic',
        'status',
        'priority',
        'estimated_hours',
        'promised_completion_at',
        'created_at',
        'admin_actions_display',
    )

    list_filter = (
        'status',
        'priority',
        'mechanic',
    )

    search_fields = (
        'title',
        'description',
        'car__registration_number',
        'mechanic__name',
    )

    autocomplete_fields = (
        'car',
        'mechanic',
    )

    readonly_fields = (
        'promised_completion_at',
        'created_at',
        'updated_at',
    )

    fieldsets = (
        (
            None,
            {
                'fields': (
                    'title',
                    'description',
                    'car',
                    'mechanic',
                    'status',
                    'priority',
                ),
            },
        ),
        (
            'Completion time',
            {
                'fields': (
                    'estimated_hours',
                    'promised_completion_at',
                ),
                'description': (
                    'Enter estimated work hours (e.g. 2.5); after you save, '
                    'promised completion is set from the task start time plus '
                    'those hours. Clear hours to remove the promised time.'
                ),
            },
        ),
        (
            'Timestamps',
            {
                'fields': ('created_at', 'updated_at'),
                'classes': ('collapse',),
            },
        ),
    )

    ordering = (
        'status',
        '-created_at',
    )

    @admin.display(description=_('Actions'), ordering=False)
    def admin_actions_display(self, obj):
        label = obj.title[:120] + ('…' if len(obj.title) > 120 else '')
        return admin_edit_delete_actions(
            obj,
            edit_title=_('Edit task "%(title)s"') % {'title': label},
            delete_title=_('Delete task "%(title)s"') % {'title': label},
        )


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    _list_display = list(DjangoUserAdmin.list_display)
    _list_display.insert(_list_display.index('username') + 1, 'shop_role_display')
    _list_display.append('user_actions_display')
    list_display = tuple(_list_display)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related('groups').select_related('mechanic_profile')

    @admin.display(description=_('Role'), ordering=False)
    def shop_role_display(self, obj):
        if obj.is_superuser:
            variant = 'superuser'
            label = _('Superuser')
        elif any(g.name == MANAGER_GROUP for g in obj.groups.all()):
            variant = 'manager'
            label = _('Manager')
        elif get_mechanic_profile(obj) is not None:
            variant = 'mechanic'
            label = _('Mechanic')
        else:
            return mark_safe('<span class="text-muted">—</span>')
        return format_html(
            '<span class="shop-role-pill shop-role-pill--{}">{}</span>',
            variant,
            label,
        )

    @admin.display(description=_('Actions'), ordering=False)
    def user_actions_display(self, obj):
        return admin_edit_delete_actions(
            obj,
            edit_title=_('Edit user %(username)s') % {'username': obj.username},
            delete_title=_('Delete user %(username)s')
            % {'username': obj.username},
        )

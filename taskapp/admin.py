from django.contrib import admin
from .models import Cars, Mechanic, Task


@admin.register(Mechanic)
class MechanicAdmin(admin.ModelAdmin):

    list_display = (
        'name',
        'specialization',
        'phone_number',
        'is_active',
        'created_at',
    )

    list_filter = (
        'is_active',
        'specialization',
    )

    search_fields = (
        'name',
        'phone_number',
        'specialization',
    )

    ordering = ('name',)


@admin.register(Cars)
class CarAdmin(admin.ModelAdmin):

    list_display = (
        'registration_number',
        'make',
        'model',
        'customer_name',
        'status',
        'created_at',
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
    )

    ordering = (
        'status',
        '-created_at',
    )

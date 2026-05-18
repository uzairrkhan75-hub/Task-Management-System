from django.contrib import admin
from .models import Cars, Mechanic, Task


@admin.register(Mechanic)
class MechanicAdmin(admin.ModelAdmin):

    list_display = (
        'name',
        'specialization',
        'availability_display',
        'on_leave',
        'manual_busy',
        'phone_number',
        'is_active',
        'created_at',
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

    @admin.display(boolean=True, description='On leave')
    def on_leave(self, obj):
        return obj.is_on_leave

    @admin.display(boolean=True, description='Manual busy')
    def manual_busy(self, obj):
        return obj.is_manually_busy

    @admin.display(description='Availability')
    def availability_display(self, obj):
        return obj.availability_label


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

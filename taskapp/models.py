from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone

# Create your models here.


class Mechanic(models.Model):
    name = models.CharField(max_length=30)
    specialization = models.CharField(max_length=30, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    is_active = models.BooleanField(default=True)
    is_on_leave = models.BooleanField(
        default=False,
        help_text='Mark when the mechanic is unavailable (leave).',
    )
    is_manually_busy = models.BooleanField(
        default=False,
        help_text='When set and there is no open task, shows as Busy.',
    )
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='mechanic_profile',
        help_text='Optional login for this mechanic (restricted to assigned tasks only).',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def is_busy(self):
        return self.tasks.exclude(status='completed').exists()

    @property
    def is_effectively_busy(self):
        return self.is_busy or self.is_manually_busy

    @property
    def availability_status(self):
        if self.is_on_leave:
            return 'on_leave'
        if self.is_effectively_busy:
            return 'busy'
        return 'free'

    @property
    def availability_label(self):
        if self.is_on_leave:
            return 'On Leave'
        if self.is_effectively_busy:
            return 'Busy'
        return 'Free'


class Cars(models.Model):
    Status_choices = [
        ('waiting', 'Waiting'),
        ('assigned', 'Assigned'),
        ('in_progress', 'In-progress'),
        ('completed', 'Completed')
    ]

    registration_number = models.CharField(max_length=20, unique=True)
    make = models.CharField(max_length=50)
    model = models.CharField(max_length=50)
    year = models.PositiveIntegerField(null=True, blank=True)
    customer_name = models.CharField(max_length=100, blank=True)
    customer_phone = models.CharField(max_length=20, blank=True)

    status = models.CharField(
        max_length=20,
        choices=Status_choices,
        default='waiting'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Car'
        verbose_name_plural = 'Cars'

    def __str__(self):
        return f"{self.registration_number} - {self.make} {self.model}"

    @property
    def repair_eta(self):
        next_task = (
            self.tasks.exclude(status='completed')
            .filter(promised_completion_at__isnull=False)
            .order_by('promised_completion_at', 'created_at')
            .first()
        )
        if next_task:
            return next_task.promised_completion_at

        return None


class Task(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]

    car = models.ForeignKey(
        Cars,
        on_delete=models.CASCADE,
        related_name='tasks'
    )

    mechanic = models.ForeignKey(
        Mechanic,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tasks'
    )

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='medium'
    )

    estimated_hours = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        null=True,
        blank=True,
        help_text='Work estimate in hours; used to calculate promised completion when you save.',
    )

    promised_completion_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['status', '-created_at']

    def save(self, *args, **kwargs):
        if self.estimated_hours:
            base_time = self.created_at or timezone.now()
            self.promised_completion_at = base_time + timedelta(
                hours=float(self.estimated_hours)
            )
        else:
            self.promised_completion_at = None

        super().save(*args, **kwargs)

        if self.mechanic_id and self.status != 'completed':
            Mechanic.objects.filter(pk=self.mechanic_id).update(
                is_manually_busy=False,
            )

    def __str__(self):
        return f"{self.title} - {self.car.registration_number}"

    @property
    def is_overdue(self):
        return (
            self.promised_completion_at
            and self.status != 'completed'
            and self.promised_completion_at < timezone.now()
        )

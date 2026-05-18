from django.db import models

# Create your models here.
class Mechanic(models.Model):
    name=models.CharField(max_length=30)
    specialization=models.CharField(max_length=30, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering=['name']
    def __str__(self):
        return self.name
class Cars(models.Model):
    Status_choices=[
        ('waiting', 'Waiting'),
        ('assigned','Assigned'),
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

    def __str__(self):
        return f"{self.registration_number} - {self.make} {self.model}"

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
            blank=True
        )

        created_at = models.DateTimeField(auto_now_add=True)
        updated_at = models.DateTimeField(auto_now=True)

        class Meta:
            ordering = ['status', '-created_at']

        def __str__(self):
            return f"{self.title} - {self.car.registration_number}"


from django import forms

from .models import Task


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = [
            'title',
            'description',
            'car',
            'mechanic',
            'status',
            'priority',
            'estimated_hours',
        ]
        widgets = {
            'status': forms.Select(
                attrs={'class': 'form-select enum-select enum-task-status'},
            ),
            'priority': forms.Select(
                attrs={'class': 'form-select enum-select enum-task-priority'},
            ),
        }

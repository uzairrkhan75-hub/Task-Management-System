from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.db.models import Exists, OuterRef

from .models import Mechanic, Task
from .rbac import users_available_for_mechanic_link


class ShopAuthenticationForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            extra = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = (extra + ' form-control').strip()


class MechanicForm(forms.ModelForm):
    class Meta:
        model = Mechanic
        fields = [
            'name',
            'specialization',
            'phone_number',
            'is_active',
            'is_on_leave',
            'is_manually_busy',
            'user',
        ]
        widgets = {
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'specialization': forms.TextInput(attrs={'class': 'form-control'}),
            'user': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        user_field = self.fields['user']
        user_field.queryset = users_available_for_mechanic_link(self.instance).order_by(
            'username',
        )
        user_field.required = False


class TaskMechanicForm(forms.ModelForm):
    """Mechanics may update progress fields only (assigned tasks)."""

    class Meta:
        model = Task
        fields = ['description', 'status', 'priority', 'estimated_hours']
        widgets = {
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'status': forms.Select(
                attrs={'class': 'form-select enum-select enum-task-status'},
            ),
            'priority': forms.Select(
                attrs={'class': 'form-select enum-select enum-task-priority'},
            ),
            'estimated_hours': forms.NumberInput(attrs={'class': 'form-control'}),
        }


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
            'mechanic': forms.Select(
                attrs={'class': 'form-select'},
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        open_tasks = Task.objects.filter(mechanic=OuterRef('pk')).exclude(
            status='completed',
        )
        if self.instance.pk:
            open_tasks = open_tasks.exclude(pk=self.instance.pk)

        mechanics = (
            Mechanic.objects.filter(is_on_leave=False)
            .annotate(has_other_open_task=Exists(open_tasks))
            .order_by('name')
        )

        free_choices = []
        busy_choices = []
        for m in mechanics:
            is_busy = m.has_other_open_task or m.is_manually_busy
            pair = (m.pk, m.name)
            if is_busy:
                busy_choices.append(pair)
            else:
                free_choices.append(pair)

        current_pk = (
            self.instance.mechanic_id
            if self.instance.pk and self.instance.mechanic_id
            else None
        )
        mechanic_pks = {p[0] for p in free_choices + busy_choices}

        if current_pk and current_pk not in mechanic_pks:
            cur = Mechanic.objects.filter(pk=current_pk).first()
            if cur:
                lbl = f'{cur.name} (on leave)'
                busy_choices.append((cur.pk, lbl))
                mechanic_pks.add(cur.pk)

        grouped = [('', self.fields['mechanic'].empty_label or '---------')]
        if free_choices:
            grouped.append(('Free mechanics', free_choices))
        if busy_choices:
            grouped.append(('Busy mechanics', busy_choices))

        mech_field = self.fields['mechanic']
        mech_field.queryset = Mechanic.objects.filter(pk__in=mechanic_pks).order_by(
            'name',
        )
        mech_field.choices = grouped

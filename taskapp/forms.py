from django import forms
from django.contrib.auth import get_user_model, password_validation
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.db.models import Exists, OuterRef

from .models import Mechanic, Task
from .rbac import MANAGER_GROUP, users_available_for_mechanic_link

User = get_user_model()


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


class ShopUserCreateForm(UserCreationForm):
    """Create login accounts from the shop UI (managers)."""

    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={'class': 'form-control'}),
    )
    first_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    last_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )

    class Meta(UserCreationForm.Meta):
        model = User

    def __init__(self, *args, acting_user=None, **kwargs):
        self.acting_user = acting_user
        super().__init__(*args, **kwargs)
        for name in ('username', 'password1', 'password2'):
            if name in self.fields:
                self.fields[name].widget.attrs.setdefault('class', 'form-control')
        if acting_user and acting_user.is_superuser:
            self.fields['is_staff'] = forms.BooleanField(
                required=False,
                initial=False,
                label='Staff (Django admin access)',
            )
            self.fields['grant_manager_role'] = forms.BooleanField(
                required=False,
                initial=False,
                label='Manager role (full shop access)',
            )

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data.get('email', '') or ''
        user.first_name = self.cleaned_data.get('first_name', '') or ''
        user.last_name = self.cleaned_data.get('last_name', '') or ''
        user.is_superuser = False
        if self.acting_user and self.acting_user.is_superuser:
            user.is_staff = self.cleaned_data.get('is_staff', False)
        else:
            user.is_staff = False
        if commit:
            user.save()
            if self.acting_user and self.acting_user.is_superuser:
                if self.cleaned_data.get('grant_manager_role'):
                    mgr_g = Group.objects.get(name=MANAGER_GROUP)
                    user.groups.add(mgr_g)
        return user


class ShopUserUpdateForm(forms.ModelForm):
    grant_manager_role = forms.BooleanField(
        required=False,
        label='Manager role (full shop access)',
    )
    new_password1 = forms.CharField(
        required=False,
        strip=False,
        label='New password',
        widget=forms.PasswordInput(
            attrs={'class': 'form-control', 'autocomplete': 'new-password'},
        ),
    )
    new_password2 = forms.CharField(
        required=False,
        strip=False,
        label='Confirm new password',
        widget=forms.PasswordInput(
            attrs={'class': 'form-control', 'autocomplete': 'new-password'},
        ),
    )

    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name')
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, acting_user=None, **kwargs):
        self.acting_user = acting_user
        super().__init__(*args, **kwargs)
        if acting_user and acting_user.is_superuser:
            self.fields['grant_manager_role'].initial = self.instance.groups.filter(
                name=MANAGER_GROUP,
            ).exists()
            self.fields['is_staff'] = forms.BooleanField(
                required=False,
                label='Staff (Django admin access)',
                initial=self.instance.is_staff,
            )
        else:
            del self.fields['grant_manager_role']

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('new_password1')
        p2 = cleaned_data.get('new_password2')
        if p1 or p2:
            if p1 != p2:
                raise ValidationError('The two password fields do not match.')
            password_validation.validate_password(p1, self.instance)
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        if self.acting_user and self.acting_user.is_superuser:
            user.is_staff = self.cleaned_data.get('is_staff', False)
        pwd = self.cleaned_data.get('new_password1')
        if pwd:
            user.set_password(pwd)
        if commit:
            user.save()
        if self.acting_user and self.acting_user.is_superuser:
            mgr_g = Group.objects.get(name=MANAGER_GROUP)
            if self.cleaned_data.get('grant_manager_role'):
                user.groups.add(mgr_g)
            else:
                user.groups.remove(mgr_g)
        return user

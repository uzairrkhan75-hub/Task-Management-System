from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.db.models import Exists, OuterRef
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from django.contrib import messages
from django.core.exceptions import PermissionDenied

from .forms import (
    MechanicForm,
    ShopAuthenticationForm,
    ShopUserCreateForm,
    ShopUserUpdateForm,
    TaskForm,
)
from .mixins import ShopAccessMixin, ShopManagerRequiredMixin
from .models import Cars, Mechanic, Task
from .rbac import (
    is_shop_manager,
    mechanic_tasks_queryset,
    resolve_shop_access_role,
)

User = get_user_model()

'''======== Create your views here========='''


class ShopLoginView(LoginView):
    template_name = 'registration/login.html'
    redirect_authenticated_user = True
    authentication_form = ShopAuthenticationForm

    def get_default_redirect_url(self):
        if resolve_shop_access_role(self.request.user) == 'mechanic':
            return reverse('task_list')
        return super().get_default_redirect_url()


@login_required
def home(request):
    role = resolve_shop_access_role(request.user)
    if role is None:
        messages.error(
            request,
            'Your account has no shop access. Ask a manager to link your '
            'login to a mechanic profile or add you to the Manager group.',
        )
        from django.contrib.auth import logout
        logout(request)
        return redirect('login')
    if role == 'mechanic':
        return redirect('task_list')
    now = timezone.now()
    tasks = Task.objects.all()
    active_tasks = tasks.exclude(status='completed')
    due_soon = active_tasks.filter(
        promised_completion_at__gte=now,
        promised_completion_at__lte=now + timedelta(hours=24),
    ).count()
    overdue_tasks = active_tasks.filter(promised_completion_at__lt=now).count()
    next_task = (
        active_tasks.filter(promised_completion_at__isnull=False)
        .order_by('promised_completion_at', 'created_at')
        .first()
    )

    cars_scope = Cars.objects.all()

    return render(
        request,
        'home.html',
        {
            'total_cars': cars_scope.count(),
            'active_tasks': active_tasks.count(),
            'due_soon': due_soon,
            'overdue_tasks': overdue_tasks,
            'next_task': next_task,
        },
    )


@login_required
def customer_eta(request):
    if not is_shop_manager(request.user):
        messages.error(request, 'Track Car is not available for mechanic accounts.')
        return redirect('task_list')
    registration_number = request.GET.get('registration_number', '').strip()
    customer_car = None
    customer_tasks = []
    lookup_error = None

    if registration_number:
        customer_car = (
            Cars.objects.prefetch_related('tasks')
            .filter(registration_number__iexact=registration_number)
            .first()
        )

        if customer_car:
            customer_tasks = list(
                customer_car.tasks.select_related('mechanic').order_by(
                    'status', '-created_at'
                )
            )
        else:
            lookup_error = 'No car found for that registration number.'

    return render(
        request,
        'customer_eta.html',
        {
            'registration_number': registration_number,
            'customer_car': customer_car,
            'customer_tasks': customer_tasks,
            'lookup_error': lookup_error,
        },
    )


'''===========CAR VIEWS=============='''


class CarListView(ShopManagerRequiredMixin, ListView):
    model = Cars
    template_name = 'cars/car_list.html'
    context_object_name = 'cars'

    def get_queryset(self):
        return Cars.objects.prefetch_related('tasks')


class CarCreateView(ShopManagerRequiredMixin, CreateView):
    model = Cars
    fields = ['registration_number', 'make', 'model']
    template_name = 'cars/car_form.html'
    success_url = reverse_lazy('car_list')


class CarUpdateView(ShopManagerRequiredMixin, UpdateView):
    model = Cars
    fields = ['registration_number', 'make', 'model']
    template_name = 'cars/car_form.html'
    success_url = reverse_lazy('car_list')


class CarDeleteView(ShopManagerRequiredMixin, DeleteView):
    model = Cars
    template_name = 'cars/car_confirm_delete.html'
    success_url = reverse_lazy('car_list')


'''========MECHANIC VIEWS======='''


class MechanicListView(ShopManagerRequiredMixin, ListView):
    model = Mechanic
    template_name = 'mechanics/mechanic_list.html'
    context_object_name = 'mechanics'

    def get_queryset(self):
        active_task = Task.objects.filter(
            mechanic=OuterRef('pk'),
        ).exclude(status='completed')
        return Mechanic.objects.annotate(
            has_active_task=Exists(active_task),
        )


class MechanicCreateView(ShopManagerRequiredMixin, CreateView):
    model = Mechanic
    form_class = MechanicForm
    template_name = 'mechanics/mechanic_form.html'
    success_url = reverse_lazy('mechanic_list')


class MechanicUpdateView(ShopManagerRequiredMixin, UpdateView):
    model = Mechanic
    form_class = MechanicForm
    template_name = 'mechanics/mechanic_form.html'
    success_url = reverse_lazy('mechanic_list')


class MechanicDeleteView(ShopManagerRequiredMixin, DeleteView):
    model = Mechanic
    template_name = 'mechanics/mechanic_confirm_delete.html'
    success_url = reverse_lazy('mechanic_list')


'''===========SHOP USER VIEWS (managers)=============='''


class ShopUserListView(ShopManagerRequiredMixin, ListView):
    model = User
    template_name = 'users/user_list.html'
    context_object_name = 'shop_users'

    def get_queryset(self):
        qs = (
            User.objects.order_by('username')
            .prefetch_related('groups')
            .select_related('mechanic_profile')
        )
        if self.request.user.is_superuser:
            return qs
        return qs.filter(is_superuser=False)


class ShopUserCreateView(ShopManagerRequiredMixin, CreateView):
    model = User
    form_class = ShopUserCreateForm
    template_name = 'users/user_form.html'
    success_url = reverse_lazy('shop_user_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['acting_user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['form_heading'] = 'Add user'
        ctx['edit_username'] = ''
        return ctx

    def form_valid(self, form):
        messages.success(self.request, f'User {form.instance.username} created.')
        return super().form_valid(form)


class ShopUserUpdateView(ShopManagerRequiredMixin, UpdateView):
    model = User
    form_class = ShopUserUpdateForm
    template_name = 'users/user_form.html'
    success_url = reverse_lazy('shop_user_list')

    def get_queryset(self):
        qs = User.objects.all()
        if self.request.user.is_superuser:
            return qs
        return qs.filter(is_superuser=False)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['acting_user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['form_heading'] = 'Edit user'
        ctx['edit_username'] = self.object.username
        return ctx

    def form_valid(self, form):
        messages.success(self.request, f'User {self.object.username} updated.')
        return super().form_valid(form)


class ShopUserDeleteView(ShopManagerRequiredMixin, DeleteView):
    model = User
    template_name = 'users/user_confirm_delete.html'
    success_url = reverse_lazy('shop_user_list')

    def get_queryset(self):
        qs = User.objects.select_related('mechanic_profile')
        if self.request.user.is_superuser:
            return qs
        return qs.filter(is_superuser=False)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.pk == request.user.pk:
            messages.error(request, 'You cannot delete your own account.')
            return redirect(self.success_url)
        username = self.object.username
        messages.success(request, f'User {username} deleted.')
        return super().delete(request, *args, **kwargs)


@login_required
@require_POST
def mechanic_set_availability(request, pk):
    if not is_shop_manager(request.user):
        raise PermissionDenied
    mechanic = get_object_or_404(Mechanic, pk=pk)

    avail = request.POST.get('availability')
    # Same rule as Mechanic.is_busy / list annotate `has_active_task`
    has_open_tasks = mechanic.is_busy

    if avail == 'on_leave':
        mechanic.is_on_leave = True
        mechanic.is_manually_busy = False
    elif avail == 'busy':
        mechanic.is_on_leave = False
        mechanic.is_manually_busy = not has_open_tasks
    elif avail == 'free':
        if has_open_tasks:
            messages.warning(
                request,
                f'{mechanic.name} still has open tasks. Complete or reassign '
                'those tasks before marking Free.',
            )
            return redirect('mechanic_list')
        mechanic.is_on_leave = False
        mechanic.is_manually_busy = False
    else:
        messages.error(request, 'Invalid status selected.')
        return redirect('mechanic_list')

    mechanic.save()
    return redirect('mechanic_list')


def _redirect_after_task_inline(request):
    next_url = request.POST.get('next')
    if next_url and url_has_allowed_host_and_scheme(
        next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return redirect(next_url)
    return redirect('task_list')


def _ensure_task_editable(request, task):
    if is_shop_manager(request.user):
        return
    from .rbac import get_mechanic_profile
    mechanic = get_mechanic_profile(request.user)
    if mechanic and task.mechanic_id == mechanic.pk:
        return
    raise PermissionDenied


@login_required
@require_POST
def task_set_status(request, pk):
    task = get_object_or_404(Task, pk=pk)
    _ensure_task_editable(request, task)
    s = request.POST.get('status')
    if s not in dict(Task.STATUS_CHOICES):
        messages.error(request, 'Invalid task status.')
        return _redirect_after_task_inline(request)
    task.status = s
    task.save()
    return _redirect_after_task_inline(request)


@login_required
@require_POST
def task_set_priority(request, pk):
    task = get_object_or_404(Task, pk=pk)
    _ensure_task_editable(request, task)
    p = request.POST.get('priority')
    if p not in dict(Task.PRIORITY_CHOICES):
        messages.error(request, 'Invalid priority.')
        return _redirect_after_task_inline(request)
    task.priority = p
    task.save()
    return _redirect_after_task_inline(request)


'''==============TASK VIEWS=============='''


class TaskListView(ShopAccessMixin, ListView):
    model = Task
    template_name = 'tasks/task_list.html'
    context_object_name = 'tasks'

    def get_queryset(self):
        return (
            mechanic_tasks_queryset(self.request.user).select_related(
                'car',
                'mechanic',
            )
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['task_status_choices'] = Task.STATUS_CHOICES
        ctx['task_priority_choices'] = Task.PRIORITY_CHOICES
        return ctx


class TaskCreateView(ShopManagerRequiredMixin, CreateView):
    model = Task
    form_class = TaskForm
    template_name = 'tasks/task_form.html'
    success_url = reverse_lazy('task_list')


class TaskUpdateView(ShopManagerRequiredMixin, UpdateView):
    model = Task
    form_class = TaskForm
    template_name = 'tasks/task_form.html'
    success_url = reverse_lazy('task_list')

    def get_queryset(self):
        return Task.objects.select_related('car', 'mechanic')


class TaskDeleteView(ShopManagerRequiredMixin, DeleteView):
    model = Task
    template_name = 'tasks/task_confirm_delete.html'
    success_url = reverse_lazy('task_list')

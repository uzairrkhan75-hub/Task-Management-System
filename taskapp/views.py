from django.db.models import Exists, OuterRef

from .forms import TaskForm
from .models import Cars, Mechanic, Task
from django.utils import timezone
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from datetime import timedelta

from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST
from django.contrib import messages
template_name = 'cars/car_form.html'
success_url = reverse_lazy('car_list')


'''======== Create your views here========='''


def home(request):
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

    return render(
        request,
        'home.html',
        {
            'total_cars': Cars.objects.count(),
            'active_tasks': active_tasks.count(),
            'due_soon': due_soon,
            'overdue_tasks': overdue_tasks,
            'next_task': next_task,
        },
    )


def customer_eta(request):
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


class CarListView(ListView):
    model = Cars
    template_name = 'cars/car_list.html'
    context_object_name = 'cars'

    def get_queryset(self):
        return super().get_queryset().prefetch_related('tasks')


class CarCreateView(CreateView):
    model = Cars
    fields = ['registration_number', 'make', 'model']
    template_name = 'cars/car_form.html'
    success_url = reverse_lazy('car_list')


class CarUpdateView(UpdateView):
    model = Cars
    fields = ['registration_number', 'make', 'model']
    template_name = 'cars/car_form.html'
    success_url = reverse_lazy('car_list')


class CarDeleteView(DeleteView):
    model = Cars
    template_name = 'cars/car_confirm_delete.html'
    success_url = reverse_lazy('car_list')


'''========MECHANIC VIEWS======='''


class MechanicListView(ListView):
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


class MechanicCreateView(CreateView):
    model = Mechanic
    fields = ['name', 'specialization', 'is_on_leave', 'is_manually_busy']
    template_name = 'mechanics/mechanic_form.html'
    success_url = reverse_lazy('mechanic_list')


class MechanicUpdateView(UpdateView):
    model = Mechanic
    fields = ['name', 'specialization', 'is_on_leave', 'is_manually_busy']
    template_name = 'mechanics/mechanic_form.html'
    success_url = reverse_lazy('mechanic_list')


class MechanicDeleteView(DeleteView):
    model = Mechanic
    template_name = 'mechanics/mechanic_confirm_delete.html'
    success_url = reverse_lazy('mechanic_list')


@require_POST
def mechanic_set_availability(request, pk):
    mechanic = get_object_or_404(Mechanic, pk=pk)
    avail = request.POST.get('availability')
    has_tasks = mechanic.tasks.exclude(status='completed').exists()

    if avail == 'on_leave':
        mechanic.is_on_leave = True
        mechanic.is_manually_busy = False
    elif avail == 'busy':
        mechanic.is_on_leave = False
        mechanic.is_manually_busy = not has_tasks
    elif avail == 'free':
        if has_tasks:
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


@require_POST
def task_set_status(request, pk):
    task = get_object_or_404(Task, pk=pk)
    s = request.POST.get('status')
    if s not in dict(Task.STATUS_CHOICES):
        messages.error(request, 'Invalid task status.')
        return _redirect_after_task_inline(request)
    task.status = s
    task.save()
    return _redirect_after_task_inline(request)


@require_POST
def task_set_priority(request, pk):
    task = get_object_or_404(Task, pk=pk)
    p = request.POST.get('priority')
    if p not in dict(Task.PRIORITY_CHOICES):
        messages.error(request, 'Invalid priority.')
        return _redirect_after_task_inline(request)
    task.priority = p
    task.save()
    return _redirect_after_task_inline(request)


'''==============TASK VIEWS=============='''


class TaskListView(ListView):
    model = Task
    template_name = 'tasks/task_list.html'
    context_object_name = 'tasks'

    def get_queryset(self):
        return super().get_queryset().select_related('car', 'mechanic')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['task_status_choices'] = Task.STATUS_CHOICES
        ctx['task_priority_choices'] = Task.PRIORITY_CHOICES
        return ctx


class TaskCreateView(CreateView):
    model = Task
    form_class = TaskForm
    template_name = 'tasks/task_form.html'
    success_url = reverse_lazy('task_list')


class TaskUpdateView(UpdateView):
    model = Task
    form_class = TaskForm
    template_name = 'tasks/task_form.html'
    success_url = reverse_lazy('task_list')


class TaskDeleteView(DeleteView):
    model = Task
    template_name = 'tasks/task_confirm_delete.html'
    success_url = reverse_lazy('task_list')

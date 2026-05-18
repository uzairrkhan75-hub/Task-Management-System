from .models import Cars, Mechanic, Task
from django.utils import timezone
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from datetime import timedelta

from django.shortcuts import render
from django.urls import reverse_lazy
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

    return render(
        request,
        'home.html',
        {
            'total_cars': Cars.objects.count(),
            'total_tasks': tasks.count(),
            'active_tasks': active_tasks.count(),
            'due_soon': due_soon,
            'overdue_tasks': overdue_tasks,
            'next_task': next_task,
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


class MechanicCreateView(CreateView):
    model = Mechanic
    fields = ['name', 'specialization']
    template_name = 'mechanics/mechanic_form.html'
    success_url = reverse_lazy('mechanic_list')


class MechanicUpdateView(UpdateView):
    model = Mechanic
    fields = ['name', 'specialization']
    template_name = 'mechanics/mechanic_form.html'
    success_url = reverse_lazy('mechanic_list')


class MechanicDeleteView(DeleteView):
    model = Mechanic
    template_name = 'mechanics/mechanic_confirm_delete.html'
    success_url = reverse_lazy('mechanic_list')


'''==============TASK VIEWS=============='''


class TaskListView(ListView):
    model = Task
    template_name = 'tasks/task_list.html'
    context_object_name = 'tasks'

    def get_queryset(self):
        return super().get_queryset().select_related('car', 'mechanic')


class TaskCreateView(CreateView):
    model = Task
    fields = ['title', 'description', 'car',
              'mechanic', 'status', 'estimated_hours']
    template_name = 'tasks/task_form.html'
    success_url = reverse_lazy('task_list')


class TaskUpdateView(UpdateView):
    model = Task
    fields = ['title', 'description', 'car',
              'mechanic', 'status', 'estimated_hours']
    template_name = 'tasks/task_form.html'
    success_url = reverse_lazy('task_list')


class TaskDeleteView(DeleteView):
    model = Task
    template_name = 'tasks/task_confirm_delete.html'
    success_url = reverse_lazy('task_list')

from django.shortcuts import render
from django.urls import reverse_lazy
template_name = 'cars/car_form.html'
success_url = reverse_lazy('car_list')
from django.views.generic import ListView, CreateView, UpdateView, DeleteView

from .models import Cars, Mechanic, Task

'''======== Create your views here========='''
def home(request):
    return render(request, 'home.html')



'''===========CAR VIEWS=============='''

class CarListView(ListView):
    model = Cars
    template_name = 'cars/car_list.html'
    context_object_name = 'cars'


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


class TaskCreateView(CreateView):
    model = Task
    fields = ['title', 'description', 'car', 'mechanic', 'status']
    template_name = 'tasks/task_form.html'
    success_url = reverse_lazy('task_list')


class TaskUpdateView(UpdateView):
    model = Task
    fields = ['title', 'description', 'car', 'mechanic', 'status']
    template_name = 'tasks/task_form.html'
    success_url = reverse_lazy('task_list')


class TaskDeleteView(DeleteView):
    model = Task
    template_name = 'tasks/task_confirm_delete.html'
    success_url = reverse_lazy('task_list')

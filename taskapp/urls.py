from django.urls import path
from . import views
from .views import (
    CarListView,
    CarCreateView,
    CarUpdateView,
    CarDeleteView,
    MechanicListView,
    MechanicCreateView,
    MechanicUpdateView,
    MechanicDeleteView,
    TaskListView,
    TaskCreateView,
    TaskUpdateView,
    TaskDeleteView,
    mechanic_set_availability,
    task_set_status,
    task_set_priority,
)

urlpatterns = [
    path('', views.home, name='home'),
    path('track-car/', views.customer_eta, name='customer_eta'),
    # Cars
    path('cars/', CarListView.as_view(), name='car_list'),
    path('cars/create/', CarCreateView.as_view(), name='car_create'),
    path('cars/<int:pk>/update/', CarUpdateView.as_view(), name='car_update'),
    path('cars/<int:pk>/delete/', CarDeleteView.as_view(), name='car_delete'),

    # Mechanics
    path('mechanics/', MechanicListView.as_view(), name='mechanic_list'),
    path('mechanics/create/', MechanicCreateView.as_view(), name='mechanic_create'),
    path('mechanics/<int:pk>/update/',
         MechanicUpdateView.as_view(), name='mechanic_update'),
    path('mechanics/<int:pk>/delete/',
         MechanicDeleteView.as_view(), name='mechanic_delete'),
    path(
        'mechanics/<int:pk>/availability/',
        mechanic_set_availability,
        name='mechanic_set_availability',
    ),

    # Tasks
    path('tasks/', TaskListView.as_view(), name='task_list'),
    path('tasks/create/', TaskCreateView.as_view(), name='task_create'),
    path('tasks/<int:pk>/update/', TaskUpdateView.as_view(), name='task_update'),
    path('tasks/<int:pk>/set-status/', task_set_status, name='task_set_status'),
    path(
        'tasks/<int:pk>/set-priority/',
        task_set_priority,
        name='task_set_priority',
    ),
    path('tasks/<int:pk>/delete/', TaskDeleteView.as_view(), name='task_delete'),
]

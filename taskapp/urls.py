from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    path('accounts/login/', views.ShopLoginView.as_view(), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('', views.home, name='home'),
    path('track-car/', views.customer_eta, name='customer_eta'),
    # Cars
    path('cars/', views.CarListView.as_view(), name='car_list'),
    path('cars/create/', views.CarCreateView.as_view(), name='car_create'),
    path('cars/<int:pk>/update/', views.CarUpdateView.as_view(), name='car_update'),
    path('cars/<int:pk>/delete/', views.CarDeleteView.as_view(), name='car_delete'),
    # Mechanics
    path('mechanics/', views.MechanicListView.as_view(), name='mechanic_list'),
    path(
        'mechanics/create/',
        views.MechanicCreateView.as_view(),
        name='mechanic_create',
    ),
    path(
        'mechanics/<int:pk>/update/',
        views.MechanicUpdateView.as_view(),
        name='mechanic_update',
    ),
    path(
        'mechanics/<int:pk>/delete/',
        views.MechanicDeleteView.as_view(),
        name='mechanic_delete',
    ),
    path('users/', views.ShopUserListView.as_view(), name='shop_user_list'),
    path(
        'users/create/',
        views.ShopUserCreateView.as_view(),
        name='shop_user_create',
    ),
    path(
        'users/<int:pk>/update/',
        views.ShopUserUpdateView.as_view(),
        name='shop_user_update',
    ),
    path(
        'users/<int:pk>/delete/',
        views.ShopUserDeleteView.as_view(),
        name='shop_user_delete',
    ),
    path(
        'mechanics/<int:pk>/availability/',
        views.mechanic_set_availability,
        name='mechanic_set_availability',
    ),
    # Tasks
    path('tasks/', views.TaskListView.as_view(), name='task_list'),
    path('tasks/create/', views.TaskCreateView.as_view(), name='task_create'),
    path('tasks/<int:pk>/update/', views.TaskUpdateView.as_view(), name='task_update'),
    path(
        'tasks/<int:pk>/set-status/',
        views.task_set_status,
        name='task_set_status',
    ),
    path(
        'tasks/<int:pk>/set-priority/',
        views.task_set_priority,
        name='task_set_priority',
    ),
    path('tasks/<int:pk>/delete/', views.TaskDeleteView.as_view(), name='task_delete'),
]

# aggregator_app/urls.py

from django.urls import path
from . import views

urlpatterns = [
    # Маршрут для главной страницы. Пустая строка '' означает корень сайта.
    path('', views.index_view, name='index'),

    # Основные эндпоинты
    path('projects/', views.ProjectListCreateAPIView.as_view(), name='project-list-create'),
    path('users/<int:user_id>/', views.UserDetailAPIView.as_view(), name='user-detail'),
    path('users/<int:user_id>/complete_task/', views.CompleteTaskAPIView.as_view(), name='complete-task'),

    # Отладочные эндпоинты
    path('ping/', views.PingAPIView.as_view(), name='ping'),
    path('debug/db/', views.DebugDBAPIView.as_view(), name='debug-db'),
    path('debug/projects/', views.DebugProjectsAPIView.as_view(), name='debug-projects'),
]
# aggregator_app/views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from django.apps import apps
from django.shortcuts import render

from .models import Project, User, Task
from .serializers import ProjectSerializer, UserSerializer
from .custom_auth import IsTelegramAuthenticated

# --- Основные API эндпоинты ---

class ProjectListCreateAPIView(APIView):
    """
    Обрабатывает GET-запросы для получения списка проектов (с фильтрацией)
    и POST-запросы для создания нового проекта.
    Эндпоинт: /projects/
    """
    def get(self, request):
        queryset = Project.objects.all()
        
        # Параметры фильтрации из URL (например, /projects/?type=channels&theme=новости)
        type_param = request.query_params.get('type')
        theme_param = request.query_params.get('theme')
        
        type_mapping = {'channels': 'channel', 'bots': 'bot', 'apps': 'mini_app'}
        
        if type_param:
            django_type = type_mapping.get(type_param.lower())
            if django_type:
                queryset = queryset.filter(type=django_type)
        
        if theme_param:
            queryset = queryset.filter(theme=theme_param)
            
        serializer = ProjectSerializer(queryset, many=True)
        return Response(serializer.data)

    def post(self, request):
        # Проверяем аутентификацию Telegram только для POST запроса
        self.permission_classes = [IsTelegramAuthenticated]
        self.check_permissions(request)

        serializer = ProjectSerializer(data=request.data)
        if serializer.is_valid():
            # Иконка не получается здесь, т.к. это медленная операция.
            # Для получения иконок используется отдельная management-команда update_avatars.
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserDetailAPIView(APIView):
    """
    Обрабатывает GET-запросы для получения информации о пользователе.
    Если пользователь не найден, он создается автоматически.
    Эндпоинт: /users/<int:user_id>/
    """
    def get(self, request, user_id):
        # get_or_create - идеальный метод для этого случая.
        # Он либо находит пользователя, либо создает его с указанными параметрами.
        user, created = User.objects.get_or_create(id=user_id)
        serializer = UserSerializer(user)
        return Response(serializer.data)

class CompleteTaskAPIView(APIView):
    """
    Обрабатывает POST-запросы для отметки задания как выполненного и начисления звезд.
    Эндпоинт: /users/<int:user_id>/complete_task/
    """
    permission_classes = [IsTelegramAuthenticated]

    def post(self, request, user_id):
        task_type = request.data.get('task_type')
        rewards = {'banner': 5, 'subscribe': 3, 'invite': 10}

        if task_type not in rewards:
            return Response({"detail": "Invalid task type"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # transaction.atomic гарантирует, что все операции с БД внутри блока
            # будут выполнены успешно, либо ни одна из них не будет выполнена.
            with transaction.atomic():
                user = User.objects.select_for_update().get(id=user_id)
                
                # update_or_create имитирует логику INSERT OR REPLACE из SQLite.
                Task.objects.update_or_create(
                    user=user,
                    task_type=task_type,
                    defaults={'completed': True}
                )
                
                user.stars += rewards[task_type]
                user.save()

            return Response({
                "status": "success",
                "stars_added": rewards[task_type]
            }, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# --- Отладочные эндпоинты ---

class PingAPIView(APIView):
    """Простой эндпоинт для проверки, что бэкенд работает."""
    def get(self, request):
        return Response({"status": "ok", "message": "Backend is running"})
    
# /debug/db
class DebugDBAPIView(APIView):
    def get(self, request):
        all_models = apps.get_models()
        tables = [model._meta.db_table for model in all_models if model._meta.app_label == 'aggregator_app']
        
        counts = {}
        for model in all_models:
            if model._meta.app_label == 'aggregator_app':
                counts[model._meta.db_table] = model.objects.count()
        
        return Response({"tables": tables, "counts": counts})

class DebugProjectsAPIView(APIView):
    """Возвращает список всех проектов в базе данных."""
    def get(self, request):
        projects = Project.objects.all()
        serializer = ProjectSerializer(projects, many=True)
        return Response(serializer.data)
    
# --- View для отображения главной страницы ---

def index_view(request):
    """
    Эта view просто отображает наш главный HTML-файл.
    """
    return render(request, 'aggregator_app/index.html')
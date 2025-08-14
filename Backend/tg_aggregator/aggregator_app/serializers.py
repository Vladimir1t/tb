# aggregator_app/serializers.py

from rest_framework import serializers
from .models import Project, User

class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = '__all__'

class UserSerializer(serializers.ModelSerializer):
    projects_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'stars', 'balance', 'projects_count']
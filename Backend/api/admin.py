from django.contrib import admin
from .database import get_db_connection

class ProjectAdmin(admin.ModelAdmin):
    def get_queryset(self, request):
        conn = get_db_connection()
        return conn.execute("SELECT * FROM aggregator_project").fetchall()

admin.site.register(ProjectAdmin)
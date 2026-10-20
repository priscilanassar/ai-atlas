from django.contrib import admin
from .models import Project

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'artist', 'category', 'year')
    search_fields = ('title', 'artist', 'description')
    list_filter = ('category', 'year')

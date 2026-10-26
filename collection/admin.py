
from django.contrib import admin
from .models import Collection


@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin):
    list_display = ('title', 'owner', 'created_at')
    search_fields = ('title', 'description')
    filter_horizontal = ('projects',)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset if request.user.is_superuser else queryset.filter(owner=request.user)

    def get_readonly_fields(self, request, obj=None):
        return () if request.user.is_superuser else ('owner',)

    def save_model(self, request, obj, form, change):
        if not request.user.is_superuser:
            obj.owner = request.user
        super().save_model(request, obj, form, change)

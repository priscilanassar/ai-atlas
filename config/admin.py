from django.contrib.admin import AdminSite
from django.contrib.admin.sites import site


class AtlasAdminSite(AdminSite):
    site_header = 'AI ATLAS'
    site_title = 'AI Atlas · Studio'
    index_title = 'Admin space'
    index_template = 'admin/atlas_index.html'
    enable_nav_sidebar = False

    def index(self, request, extra_context=None):
        from archive.models import Project
        from collection.models import Collection

        context = dict(extra_context or {})
        can_view_projects = request.user.has_perm('archive.view_project') or request.user.has_perm('archive.change_project')
        can_view_collections = request.user.has_perm('collection.view_collection') or request.user.has_perm('collection.change_collection')
        collections = Collection.objects.all()
        if not request.user.is_superuser:
            collections = collections.filter(owner=request.user)
        context.update({
            'project_count': Project.objects.count() if can_view_projects else None,
            'collection_count': collections.count() if can_view_collections else None,
            'artist_count': Project.objects.values('artist').distinct().count() if can_view_projects else None,
            'recent_projects': Project.objects.order_by('-created_at')[:6] if can_view_projects else [],
            'can_view_projects': can_view_projects,
            'can_add_project': request.user.has_perm('archive.add_project'),
        })
        return super().index(request, context)


# Keep the existing model registrations, including Django's user and group admins.
atlas_admin = AtlasAdminSite(name='admin')
for model, model_admin in site._registry.items():
    atlas_admin.register(model, model_admin.__class__)

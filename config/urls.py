"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""


from django.contrib import admin
from django.urls import path, include
from .views import home
from archive.views import archive
from .admin import atlas_admin
from django.views.generic import RedirectView
from django.conf import settings
from django.conf.urls.static import static
from archive.views import project_detail, project_delete, projects_bulk_delete

urlpatterns = [
    path('admin/', atlas_admin.urls),
    path('', home, name='home'),
    path('projects/<int:pk>/', project_detail, name='project_detail'),
    path('projects/<int:pk>/delete/', project_delete, name='project_delete'),
    path('projects/delete-selected/', projects_bulk_delete, name='projects_bulk_delete'),
    path('atlas/', RedirectView.as_view(pattern_name='home', query_string=True), name='atlas'),
    path('archive/', RedirectView.as_view(pattern_name='home', query_string=True), name='archive'),
    path('collection/', include('collection.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

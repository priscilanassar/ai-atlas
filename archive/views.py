
from django.shortcuts import render, get_object_or_404
from collection.forms import CollectionForm
from collection.models import Collection
from .models import Project
from django.contrib import messages
from django.contrib.admin.models import LogEntry, DELETION
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import redirect
from django.views.decorators.http import require_http_methods, require_POST
from django.http import HttpResponseBadRequest


def can_delete_projects(user):
    return user.is_active and user.is_staff and user.has_perm('archive.delete_project')


@require_http_methods(['GET', 'POST'])
def project_delete(request, pk):
    if not can_delete_projects(request.user):
        raise PermissionDenied
    project = get_object_or_404(Project, pk=pk)
    if request.method == 'POST':
        title = project.title
        with transaction.atomic():
            LogEntry.objects.log_actions(request.user.pk, [project], DELETION)
            project.delete()
        messages.success(request, f'“{title}” was deleted from the Atlas.')
        return redirect('home')
    return render(request, 'project_delete.html', {'project': project})


@require_POST
def projects_bulk_delete(request):
    if not can_delete_projects(request.user):
        raise PermissionDenied
    raw_ids = request.POST.getlist('project_ids')
    if not raw_ids or len(raw_ids) > 1200 or any(not value.isdecimal() or len(value) > 10 for value in raw_ids):
        return HttpResponseBadRequest('Select between 1 and 1200 valid projects.')
    ids = set(map(int, raw_ids))
    with transaction.atomic():
        projects = list(Project.objects.select_for_update().filter(pk__in=ids).order_by('title', 'pk'))
        if len(projects) != len(ids):
            return HttpResponseBadRequest('Some selected projects no longer exist. Return to the Atlas and select again.')
        if request.POST.get('confirm') == 'delete':
            LogEntry.objects.log_actions(request.user.pk, projects, DELETION)
            Project.objects.filter(pk__in=ids).delete()
            messages.success(request, f'{len(projects)} projects were deleted from the Atlas.')
            return redirect('home')
    return render(request, 'projects_bulk_delete.html', {'projects': projects})


def project_detail(request, pk):
    project = get_object_or_404(Project, pk=pk)
    return render(request, 'project_detail.html', {
        'project': project,
        'can_delete_projects': can_delete_projects(request.user),
        'manageable_projects': Project.objects.only('pk', 'title', 'artist', 'image', 'cover_file', 'thumbnail_file', 'thumbnail_source').order_by('title') if can_delete_projects(request.user) else [],
        'collections': Collection.objects.filter(owner=request.user) if request.user.is_authenticated else [],
        'collection_form': CollectionForm(),
        'related_projects': Project.objects.exclude(pk=pk).filter(category=project.category).order_by('-created_at')[:4],
    })

def archive(request):
    projects = Project.objects.all().order_by('-created_at')

    category = request.GET.get('category', '')
    search = request.GET.get('search', '')

    if category:
        projects = projects.filter(category=category)

    if search:
        projects = projects.filter(title__icontains=search)

    return render(request, 'archive.html', {
        'projects': projects,
        'category': category,
        'search': search,
    })

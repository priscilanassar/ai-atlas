
from django.shortcuts import render
from .models import Project

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

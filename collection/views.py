
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.views.decorators.http import require_POST
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.db import transaction

from .models import Collection
from .forms import CollectionForm
from archive.models import Project


@login_required
def collections_list(request):
    collections = Collection.objects.filter(owner=request.user).order_by('-created_at')

    return render(request, 'collection.html', {
        'collections': collections
    })


@login_required
def collection_detail(request, pk):
    collection = get_object_or_404(Collection, pk=pk, owner=request.user)

    return render(request, 'collection_detail.html', {
        'collection': collection,
        'projects': collection.projects.all()
    })


def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)

        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('my_collections')
    else:
        form = UserCreationForm()

    return render(request, 'signup.html', {'form': form})


@login_required
def my_collections(request):
    collections = Collection.objects.filter(
        owner=request.user
    ).order_by('-created_at')

    return render(request, 'my_collections.html', {
        'collections': collections
    })


@login_required
def create_collection(request):
    if request.method == 'POST':
        form = CollectionForm(request.POST)

        if form.is_valid():
            project = None
            if request.POST.get('project_id'):
                project = get_object_or_404(Project, pk=request.POST['project_id'])
            with transaction.atomic():
                collection = form.save(commit=False)
                collection.owner = request.user
                collection.save()
                if project:
                    collection.projects.add(project)

            if request.POST.get('from_atlas') == '1':
                messages.success(request, 'Collection created.' + (' Project saved.' if project else ''))
                return redirect('home')

            return redirect('my_collections')
    else:
        form = CollectionForm()

    return render(request, 'create_collection.html', {
        'form': form
    })


@login_required
@require_POST
def save_project(request, project_id):
    project = get_object_or_404(Project, pk=project_id)

    collection = get_object_or_404(
        Collection,
        pk=request.POST.get('collection_id'),
        owner=request.user
    )

    collection.projects.add(project)

    if request.POST.get('from_atlas') == '1':
        messages.success(request, 'Project saved to your collection.')
        return redirect('home')

    return redirect('collection_detail', pk=collection.pk)


@login_required
@require_http_methods(['GET', 'POST'])
def delete_collection(request, pk):
    collection = get_object_or_404(Collection, pk=pk, owner=request.user)
    if request.method == 'POST':
        title = collection.title
        collection.delete()
        messages.success(request, f'Collection "{title}" deleted. Projects remain in the Atlas.')
        return redirect('my_collections')
    return render(request, 'delete_collection.html', {'collection': collection})

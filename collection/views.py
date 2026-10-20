
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.views.decorators.http import require_POST

from .models import Collection
from .forms import CollectionForm
from archive.models import Project


def collections_list(request):
    collections = Collection.objects.all().order_by('-created_at')

    return render(request, 'collection.html', {
        'collections': collections
    })


def collection_detail(request, pk):
    collection = get_object_or_404(Collection, pk=pk)

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
            collection = form.save(commit=False)
            collection.owner = request.user
            collection.save()

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

    return redirect('collection_detail', pk=collection.pk)

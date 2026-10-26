
from django.urls import path
from . import views

urlpatterns = [
    path('', views.collections_list, name='collection'),
    path('my/', views.my_collections, name='my_collections'),
    path('new/', views.create_collection, name='create_collection'),
    path('signup/', views.signup, name='signup'),
    path('save/<int:project_id>/', views.save_project, name='save_project'),
    path('<int:pk>/', views.collection_detail, name='collection_detail'),
    path('<int:pk>/delete/', views.delete_collection, name='delete_collection'),
]

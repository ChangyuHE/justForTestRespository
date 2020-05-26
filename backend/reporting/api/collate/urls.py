from django.urls import path
from . import views

app_name = 'collate'
urlpatterns = [
    path('', views.ImportFileView.as_view(), name='import'),
    path('create/', views.CreateEntitiesView.as_view(), name='create'),
    path('form/', views.index, name='index'),
]

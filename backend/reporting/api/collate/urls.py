from django.urls import path
from . import views

app_name = 'collate'
urlpatterns = [
    path('', views.index, name='index'),
]

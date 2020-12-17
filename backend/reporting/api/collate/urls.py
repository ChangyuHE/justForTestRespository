from django.urls import path
from . import views

app_name = 'collate'
urlpatterns = [
    path('', views.ImportFileView.as_view(), name='import'),
    path('create/', views.CreateEntitiesView.as_view(), name='create'),
    path('form/', views.index, name='index'),
    path('merge/', views.MergeValidationsView.as_view(), name='merge'),
    path('clone/', views.CloneValidationsView.as_view(), name='clone'),
    path('gta-short-url/', views.ParseShortUrlView.as_view(), name='gta-short-url'),
    path('test-run-check/', views.CheckTestRunExist.as_view(), name='test-run-check'),

]

from django.urls import path
from . import views

urlpatterns = [
    path('test_verifier/import/', views.ImportView.as_view()),
    path('test_verifier/features_data/', views.SubFeatureListView.as_view()),
    path('test_verifier/features_data/<int:pk>/', views.SubFeatureDetailView.as_view()),
    path('test_verifier/codecs/', views.CodecListView.as_view()),
    path('test_verifier/categories/', views.CategoryListView.as_view()),
    path('test_verifier/features/', views.FeatureListView.as_view())
]

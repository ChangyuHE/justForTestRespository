from django.urls import path
from . import views

urlpatterns = [
    path('test_verifier/import/', views.ImportView.as_view()),
    path('test_verifier/codecs/', views.CodecListView.as_view()),
    path('test_verifier/categories/', views.FeatureCategoryListView.as_view()),
    path('test_verifier/features/', views.FeatureListView.as_view()),
    path('test_verifier/features_data/', views.SubFeatureListCreateView.as_view()),
    path('test_verifier/features_data/<int:pk>/', views.SubFeatureUpdateView.as_view()),
]
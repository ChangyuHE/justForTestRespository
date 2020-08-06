from django.urls import path
from . import views

urlpatterns = [
    path('test_verifier/import/', views.ImportView.as_view()),
    path('test_verifier/features_data/', views.SubFeatureListView.as_view()),
    path('test_verifier/features_data/add/', views.SubFeatureAddView.as_view()),
    path('test_verifier/features_data/<int:pk>/', views.SubFeatureGetDeleteView.as_view()),
    path('test_verifier/features_data/update/<int:pk>/', views.SubFeatureUpdateDetailsView.as_view()),
]

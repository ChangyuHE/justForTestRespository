from django.urls import path
from . import views

urlpatterns = [
    # SubFeature data
    path('test_verifier/import/', views.ImportView.as_view()),
    path('test_verifier/codecs/', views.CodecListView.as_view()),
    path('test_verifier/categories/', views.FeatureCategoryListView.as_view()),
    path('test_verifier/features/', views.FeatureListView.as_view()),
    path('test_verifier/features_data/', views.SubFeatureListCreateView.as_view()),
    path('test_verifier/features_data/<int:pk>/', views.SubFeatureUpdateView.as_view()),

    #  SubFeatures Coverage Rules
    path('test_verifier/coverage/rules/', views.RuleListCreateView.as_view()),
    path('test_verifier/coverage/rules/<int:pk>', views.RuleUpdateDestroyView().as_view()),
    path('test_verifier/coverage/rule_groups/', views.RuleGroupListCreateView.as_view()),
    path('test_verifier/coverage/rule_groups/<int:pk>', views.RuleGroupsUpdateView.as_view()),
]
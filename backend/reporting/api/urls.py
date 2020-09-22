from django.urls import path, include, re_path
from django.conf import settings
from django.contrib import admin
from django.conf.urls.static import static

from rest_framework_swagger.views import get_swagger_view

from api import views
from api.view import feature_mapping

schema_view = get_swagger_view(title='Reporting API')

urlpatterns = [
    path('', views.index, name='index'),
    path('api/', schema_view),
    path('test', views.test, name='test'),

    # Users
    path('api/users/current/', views.CurrentUser.as_view(), name='user-current'),
    path('api/users/', views.UserList.as_view(), name='user-list'),

    path('api/validations/', views.ValidationsView.as_view()),
    path('api/validations/flat/', views.ValidationsFlatView.as_view()),
    path('api/validations/structure', views.ValidationsStructureView.as_view()),
    path('api/validations/hard_delete/<int:pk>', views.ValidationsDeleteByIdView.as_view()),

    path('api/validations/mappings/', views.ValidationMappings.as_view()),

    # Reports
    re_path(r'^api/report/best/(?P<id>.+)$', views.ReportBestView.as_view()),   # optional param "report=excel"
    re_path(r'^api/report/last/(?P<id>.+)$', views.ReportLastView.as_view()),   # optional param "report=excel"
    re_path(r'^api/report/compare/(?P<id>.+)$', views.ReportCompareView.as_view()),     # optional param "report=excel"
    re_path(r'^api/report/search/$', views.ReportFromSearchView.as_view()),  # mandatory param "query"
    path('api/report/indicator/', views.ReportIndicatorView.as_view()),

    # returns additional_parameters field for Result with given pk
    # end extra info about this result
    path('api/report/extra-data/<int:pk>', views.ExtraDataView.as_view(), name='api-extra-data'),

    # Import
    # with mandatory parameters model, fields, emails (staff emails), requester
    path('api/objects/request-creation/', views.RequestModelCreation.as_view()),
    path('api/import/', include('api.collate.urls')),

    # Feature mapping
    # .. import
    path('api/feature_mapping/form/', feature_mapping.feature_mapping_form),   # debug only
    path('api/feature_mapping/import/', feature_mapping.FeatureMappingPostView.as_view(), name='fmt-import'),

    # .. mappings
    path('api/feature_mapping/table/', feature_mapping.FeatureMappingTableView.as_view()),
    path('api/feature_mapping/<int:pk>/', feature_mapping.FeatureMappingDetailsView.as_view()),
    path('api/feature_mapping/export/<int:pk>/', feature_mapping.FeatureMappingExportView.as_view()),
    path('api/feature_mapping/', feature_mapping.FeatureMappingListView.as_view()),
    path('api/feature_mapping/conflicts/', feature_mapping.FeatureMappingConflictCheckView.as_view()),

    # .. rules
    path('api/feature_mapping/rules/table/', feature_mapping.FeatureMappingRuleTableView.as_view()),
    path('api/feature_mapping/rules/<int:pk>/', feature_mapping.FeatureMappingRuleDetailsView.as_view()),
    path('api/feature_mapping/rules/', feature_mapping.FeatureMappingRuleView.as_view()),

    # .. rules components
    path('api/milestone/table/', feature_mapping.FeatureMappingMilestoneTableView.as_view()),
    path('api/milestone/<int:pk>/', feature_mapping.FeatureMappingMilestoneDetailsView.as_view()),
    path('api/milestone/', feature_mapping.FeatureMappingMilestoneView.as_view()),

    path('api/feature/table/', feature_mapping.FeatureMappingFeatureTableView.as_view()),
    path('api/feature/<int:pk>/', feature_mapping.FeatureMappingFeatureDetailsView.as_view()),
    path('api/feature/', feature_mapping.FeatureMappingFeatureView.as_view()),

    path('api/scenario/table/', feature_mapping.FeatureMappingScenarioTableView.as_view()),
    path('api/scenario/<int:pk>/', feature_mapping.FeatureMappingScenarioDetailsView.as_view()),
    path('api/scenario/', feature_mapping.FeatureMappingScenarioView.as_view()),

    # Common
    path('api/component/table/', views.ComponentTableView().as_view()),
    path('api/component/', views.ComponentView().as_view()),

    path('api/generation/table/', views.GenerationTableView().as_view()),
    path('api/generation/', views.GenerationView().as_view()),

    path('api/platform/table/', views.PlatformTableView().as_view()),
    path('api/platform/', views.PlatformView().as_view()),

    path('api/os/table/', views.OsTableView().as_view()),
    path('api/os/', views.OsView().as_view()),

    path('api/env/table/', views.EnvTableView().as_view()),
    path('api/env/', views.EnvView().as_view()),

    path('api/codec/table/', views.CodecTableView().as_view()),
    path('api/codec/<int:pk>/', views.CodecDetailsView.as_view()),
    path('api/codec/', views.CodecView().as_view()),

    # Test Verifier
    path('', include('test_verifier.urls')),

    path('admin/', admin.site.urls),
]\
    + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) \
    + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns

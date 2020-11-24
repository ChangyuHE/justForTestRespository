from django.urls import path, include, re_path, register_converter
from django.conf import settings
from django.contrib import admin
from django.conf.urls.static import static

from rest_framework_swagger.views import get_swagger_view

from api import views
from api.view import feature_mapping

from . import converters

register_converter(converters.CommaSeparatedOptionalPathConverter, 'list')
register_converter(converters.CommaSeparatedIntegersPathConverter, 'int_list')


schema_view = get_swagger_view(title='Reporting API')

urlpatterns = [
    path('', views.index, name='index'),
    path('api/', schema_view),
    path('test', views.test, name='test'),

    # Users
    path('api/users/current/', views.CurrentUser.as_view(), name='user-current'),
    path('api/users/', views.UserList.as_view(), name='user-list'),
    path('api/users/current/profile/', views.ProfileView.as_view()),
    path('api/users/current/profile/<int:pk>', views.ProfileDetailsView.as_view()),

    path('api/validations/', views.ValidationsView.as_view()),
    path('api/validations/flat/', views.ValidationsFlatView.as_view()),
    path('api/validations/structure', views.ValidationsStructureView.as_view()),
    path('api/validations/hard_delete/<int:pk>', views.ValidationsDeleteByIdView.as_view()),

    path('api/validations/mappings/', views.ValidationMappings.as_view()),

    # Reports
    path('api/report/best/<int_list:val_pks>//', views.ReportBestView.as_view(), name="best-report-special"),  # optional param "report=excel"
    path('api/report/best/<int_list:val_pks>/<int_list:fmt_pks>/', views.ReportBestView.as_view(), name="best-report"),  # optional param "report=excel"
    path('api/report/last/<int_list:val_pks>//', views.ReportLastView.as_view(), name="last-report-special"),  # optional param "report=excel"
    path('api/report/last/<int_list:val_pks>/<int_list:fmt_pks>/', views.ReportLastView.as_view(), name="last-report"),  # optional param "report=excel"
    re_path(r'^api/report/search/$', views.ReportFromSearchView.as_view()),  # mandatory param "query"
    path('api/report/indicator/<int:id>/', views.ReportIndicatorView.as_view()),
    path('api/report/compare/<int_list:val_pks>//', views.ReportCompareView.as_view(), name="cmp-view-special"),  # optional param "report=excel"
    path('api/report/compare/<int_list:val_pks>/<int_list:fmt_pks>/', views.ReportCompareView.as_view(), name="cmp-view"),  # optional param "report=excel"
    path('api/report/extra-data/<list:ti_pks>/', views.ExtraDataView.as_view(), name='api-extra-data'),
    path('api/report/issues/<int:pk>/', views.ReportIssuesView.as_view(), name="issues-report"),  # optional param "report=excel"

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
    path('api/feature_mapping/clone/<int:pk>/', feature_mapping.FeatureMappingCloneView.as_view()),
    path('api/feature_mapping/export/<int:pk>/', feature_mapping.FeatureMappingExportView.as_view()),
    path('api/feature_mapping/', feature_mapping.FeatureMappingListView.as_view()),
    path('api/feature_mapping/conflicts/', feature_mapping.FeatureMappingConflictCheckView.as_view()),
    path('api/feature_mapping/<int:pk>/rules_conflicts/', feature_mapping.FeatureMappingRulesConflictCheckView.as_view()),

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
    path('api/result_feature/', views.ResultFeatureView.as_view(), name='result_feature'),
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

    path('api/result/', views.ResultListView().as_view()),
    path('api/result/<int:pk>/', views.ResultView().as_view()),
    path('api/result/update/<int:pk>/', views.ResultUpdateView.as_view()),
    path('api/result/bulk_update/', views.ResultBulkListUpdateView.as_view()),
    path('api/result/history/<int:pk>/', views.ResultHistoryView().as_view()),

    path('api/driver/', views.DriverView().as_view()),
    path('api/status/', views.StatusView().as_view()),
    path('api/scenario_asset/', views.ScenarioAssetView().as_view()),
    path('api/lucas_asset/', views.LucasAssetView().as_view()),
    path('api/msdk_asset/', views.MsdkAssetView().as_view()),
    path('api/fulsim_asset/', views.FulsimAssetView().as_view()),
    path('api/simics/', views.SimicsView().as_view()),

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

from django.conf.urls import url
from django.urls import path, include
from rest_framework.urlpatterns import format_suffix_patterns
from django.conf import settings
from django.contrib import admin
from django.conf.urls.static import static

from rest_framework_swagger.views import get_swagger_view

from api import views

schema_view = get_swagger_view(title='Reporting API')

urlpatterns = [
    url('^$', views.index, name='index'),
    url(r'^api/$', schema_view),
    url(r'^test$', views.test, name='test'),

    # Users
    url(r'^api/users/current/$', views.CurrentUser.as_view(), name='user-current'),
    url(r'^api/users/(?P<username>.+)/$', views.UserDetail.as_view(), name='user-detail'),
    url(r'^api/users/$', views.UserList.as_view(), name='user-list'),

    url(r'^api/validations/$', views.ValidationsView.as_view()),
    url(r'^api/validations/flat$', views.ValidationsFlatView.as_view()),
    url(r'^api/validations/structure$', views.ValidationsStructureView.as_view()),
    url(r'^api/validations/hard_delete/(?P<pk>.+)$', views.ValidationsDeleteByIdView.as_view()),

    # reports
    url(r'^api/report/best/(?P<id>.+)$', views.ReportBestView.as_view()),   # with optional param "report=excel"
    url(r'^api/report/last/(?P<id>.+)$', views.ReportLastView.as_view()),   # with optional param "report=excel"
    url(r'^api/report/compare/(?P<id>.+)$', views.ReportCompareView.as_view()),   # with optional param "report=excel"

    # import
    path('api/import/', include('api.collate.urls')),

    path('admin/', admin.site.urls),
]\
    + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) \
    + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns

urlpatterns = format_suffix_patterns(urlpatterns)

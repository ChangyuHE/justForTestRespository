from django.conf.urls import url
from django.urls import path, include
from rest_framework.urlpatterns import format_suffix_patterns
from django.conf import settings
from django.contrib import admin
from django.conf.urls.static import static

from rest_framework_swagger.views import get_swagger_view

from api import views
from api.collate import views as import_views

schema_view = get_swagger_view(title='Reporting API')


urlpatterns = [
    url('^$', views.index, name='index'),

    url(r'^api/$', schema_view),
    url(r'^api/validations/$', views.ValidationsView.as_view()),
    url(r'^api/validations/flat$', views.ValidationsFlatView.as_view()),

    # reports
    url(r'^api/report/best/(?P<id>.+)$', views.ReportBestView.as_view()),   # with optional param "report=excel"

    # import
    url(r'^api/import/', import_views.ImportFromFile.as_view(), name='import'),

    path('admin/', admin.site.urls),
]\
    + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) \
    + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) \
#    + [url(r'^.*$', views.PassToVue.as_view()),]


if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns

urlpatterns = format_suffix_patterns(urlpatterns)

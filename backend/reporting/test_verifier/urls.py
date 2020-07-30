from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'', views.ImportView.as_view()),
]
